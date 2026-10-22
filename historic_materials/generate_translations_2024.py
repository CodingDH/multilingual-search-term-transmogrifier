# Standard library imports
import codecs
import html
import json
import os
import time
import warnings
from typing import List, Tuple
import ast

# Local application/library specific imports
import apikey
# Related third-party imports
import pandas as pd
import requests
import arabic_reshaper
from bidi.algorithm import get_display
from bs4 import BeautifulSoup
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from easynmt import EasyNMT
from transformers import AutoTokenizer
from rich.console import Console
from tqdm import tqdm
from openai import OpenAI
import wikipediaapi
import sys
sys.path.append("..")
from data_generation_scripts.utils import get_data_directory_path, read_csv_file
warnings.filterwarnings('ignore')
# Load Google Cloud credentials. You can get your own credentials by following the instructions here: https://cloud.google.com/translate/docs/setup and saving them with apikey.save("GOOGLE_TRANSLATE_CREDENTIALS", "path/to/your/credentials.json")
google_translate_key_path = apikey.load("GOOGLE_TRANSLATE_CREDENTIALS")
credentials = service_account.Credentials.from_service_account_file(
	google_translate_key_path, scopes=["https://www.googleapis.com/auth/cloud-platform"],
)

translate_client = translate.Client(credentials=credentials)

openai_key_path = apikey.load("CODING_DH_OPENAI_KEY")
openai_project_id = apikey.load("CODING_DH_OPENAI_PROJECT_ID")
openai_organization_id = apikey.load("CODING_DH_OPENAI_ORGANIZATION_ID")
client = OpenAI(
	api_key=openai_key_path,
	project=openai_project_id,
	organization=openai_organization_id
)

console = Console()

# Initialize the EasyNMT model once
model = EasyNMT('opus-mt')

def check_detect_language(row: pd.Series, is_repo:bool=False) -> pd.Series:
	"""
	Checks the detected language of a row of text using Google Cloud Translate API

	Parameters
	----------
	row : pd.Series
		A row of a dataframe with a text column
	is_repo : bool
		A boolean indicating whether the text is a repo description or a bio
	Returns a series with the detected language and confidence score
	"""
	text = row.description if is_repo else row.bio
	if pd.notna(text) and len(text) > 1:  # Additional check if text is not NaN
		try:
			result = translate_client.detect_language(text)
			row['detected_language'] = result['language']
			row['detected_language_confidence'] = result['confidence']
		except Exception as e:
			console.print(f"Error detecting language for {text}: {e}", style="bold red")
			row['detected_language'] = None
			row['detected_language_confidence'] = None
	else:
		row['detected_language'] = None
		row['detected_language_confidence'] = None
	return row

def get_directionality(directionality_path: str) -> pd.DataFrame:
	"""
	Function to get language directionality from Wikimedia
	
	Parameters
	----------
	directionality_path : str
	Returns a dataframe with language directionality
	"""
	# Read in the directionality data if it exists, otherwise scrape it from Wikimedia
	if os.path.exists(directionality_path):
		df = read_csv_file(directionality_path)
	else:
		# Get the directionality data from Wikimedia using BeautifulSoup
		url = "https://meta.wikimedia.org/wiki/Template:List_of_language_names_ordered_by_code"
		response = requests.get(url, timeout=10)
		soup = BeautifulSoup(response.text, 'html.parser')
		table = soup.find_all('table')[0]
		df = pd.read_html(str(table))[0]
		df.to_csv(
			directionality_path, index=False)
	return df

def is_enmt_model_available(target_lang: str) -> bool:
	"""
	Function to check if a model is available for a target language in EasyNMT

	Parameters
	----------
	target_lang : str
		A target language code
	Returns a boolean indicating whether the model is available
	"""
	model_name = f"Helsinki-NLP/opus-mt-en-{target_lang}"
	try:
		# Attempt to load the model tokenizer to check availability
		_ = AutoTokenizer.from_pretrained(model_name)
		return True
	except Exception as e:
		console.print(f"Model not available for {target_lang}: {e}", style="bold red")
		return False

def get_gt_translation(row: pd.Series) -> pd.Series:
	"""
	Function to get translations of terms

	Parameters
	----------
	row : pd.Series
		A row of a dataframe with terms and a language
	
	Returns
	-------
	pd.Series
		A series with the translated terms
	"""
	time.sleep(1)  # Add a delay to avoid API rate limits
	try:
		dh_terms = row.term_source
		target_language = row.language
		console.print(f"Translating {dh_terms} to {target_language}", style="bold green")
		
		# Translate terms in bulk
		text_results = translate_client.translate(dh_terms, target_language=target_language)
		
		# Match translations explicitly with the original terms
		translated_terms = [result['translatedText'] for result in text_results]
		row['gt_translated_term'] = list(zip(dh_terms, translated_terms))
	except Exception as e:
		console.print(f"Error translating {dh_terms} to {target_language}: {e}", style="bold red")
		row['gt_translated_term'] = list(zip(dh_terms, [None] * len(dh_terms)))  # Handle error by returning a list of None
	
	return row

def get_enmt_translation(row: pd.Series) -> pd.Series:
	"""
	Function to get translations of terms using EasyNMT

	Parameters
	----------
	row : pd.Series
		A row of a dataframe with terms and a language
	
	Returns
	-------
	pd.Series
		A series with the translated terms
	"""
	time.sleep(1)  # Add a delay to avoid rate limits or excessive load
	try:
		dh_terms = row.term_source
		target_language = row.language
		console.print(f"Translating {dh_terms} to {target_language}", style="bold green")
		
		# Check if the model is available for the target language
		if is_enmt_model_available(target_language):
			# Translate terms in bulk
			translated_terms = model.translate(dh_terms, target_lang=target_language, source_lang='en')
			row['enmt_translated_term'] = list(zip(dh_terms, translated_terms))
		else:
			console.print(f"No model available for {target_language}. Skipping translation.", style="bold yellow")
			row['enmt_translated_term'] = list(zip(dh_terms, [None] * len(dh_terms)))
	except Exception as e:
		console.print(f"Error translating {dh_terms} to {target_language}: {e}", style="bold red")
		row['enmt_translated_term'] = list(zip(dh_terms, [None] * len(dh_terms)))  # Handle error by returning a list of None
	
	return row

def get_openai_translation(row: pd.Series) -> pd.Series:
	"""
	Function to get translations of terms using the OpenAI API.

	Parameters
	----------
	row : pd.Series
		A row of a dataframe with terms and a language.

	Returns
	-------
	pd.Series
		A series with the translated terms from OpenAI.
	"""
	time.sleep(1)  # Avoid hitting API rate limits
	try:
		term_source = row.term_source
		language_name = row.language_name
		language_code = row.code
		gt_translated_term = row.gt_translated_term
		enmt_translated_term = row.enmt_translated_term

		console.print(f"Translating {term_source} to {language_name} using OpenAI API", style="bold green")

		# Define the base content for the user message
		user_content = (
			f"You speak the following language: {language_name} (ISO code: {language_code}). "
			f"How would you translate the term '{term_source}' into {language_name}? "
		)

		# Add Google Translate suggestion if it exists
		if gt_translated_term:
			user_content += f"When making your translation, you can consider the Google Translate suggestion '{gt_translated_term}'"

		# Add ENMT suggestion if it exists
		if enmt_translated_term:
			user_content += f" and the ENMT suggestion '{enmt_translated_term}', but feel free to modify or refine them"

		# Add the final instruction
		user_content += ". Please return your answer in this format: {'translated_term': 'your final term here'}"

		# Define sample messages
		prompt_messages = [
			{"role": "system", "content": f"You are a {term_source} scholar who speaks many languages."},
			{"role": "user", "content": user_content}
		]

		# Call the OpenAI Chat API directly using the `openai` module
		chat_completion = client.chat.completions.create(
			model="gpt-4o",
			messages=prompt_messages,
		)
		message_content = chat_completion.choices[0].message.content
		row['openai_translated_term'] = ast.literal_eval(message_content)['translated_term']
	except Exception as e:
		console.print(f"Error translating {term_source} to {language_name} using OpenAI: {e}", style="bold red")
		row['openai_translated_term'] = None

	return row

def check_if_wikipedia_page_exists(term_source: str) -> dict:
	"""
	Check if a Wikipedia page exists for a given term.

	Parameters
	----------
	term_source : str
		The term to check for in Wikipedia.

	Returns
	-------
	dict
		A dictionary with translations of the term.
	"""
	# Currently hardcoding for english wikipedia
	wiki_wiki = wikipediaapi.Wikipedia(
		language='en', 
		user_agent='MyProject/1.0 (https://example.org/myproject/; myemail@example.org)'
	)
	# Fetch the Wikipedia page
	page = wiki_wiki.page(term_source)

	if not page.exists():
		console.print(f"Page '{term_source}' does not exist in English Wikipedia.", style="bold red")
		return {}

	console.print(f"Page '{term_source}' exists in English Wikipedia.", style="bold green")
	# Get available translations in other languages
	translations = page.langlinks
	console.print(f"Has this number of {len(translations)} translated pages", style="bold green")
	keep_page = console.input("Do you want to keep this page? (y/n): ")
	if keep_page == 'n':
		return {}
	else:
		translation_dict = {lang: translations[lang].title for lang in translations}
		return translation_dict


def generate_initial_terms(target_terms: list, data_directory_path: str, process_dh: bool, use_gt_translate: bool, use_enmt_translate: bool, use_openai_translate: bool, use_wikipedia: bool) -> pd.DataFrame:
	"""
	Generate a dataframe with translated terms. This function assumes you want to at the very least translate Digital Humanities.

	Parameters
	----------
	target_terms : list
		A list of terms to translate in all ISO 639-1 languages.
	data_directory_path : str
		A path to the directory with the datasets.
	process_dh : bool
		A boolean indicating whether Digital Humanities terms already exist.
	use_gt_translate : bool
		A boolean indicating whether to use Google Cloud Translate.
	use_enmt_translate : bool
		A boolean indicating whether to use EasyNMT.
	use_openai_translate : bool
		A boolean indicating whether to use OpenAI API.
	use_wikipedia : bool
		A boolean indicating whether to check for Wikipedia pages.

	Returns
	-------
	pd.DataFrame
		A dataframe with translated terms.
	"""
	# Load ISO 639-1 languages
	iso_languages_path = os.path.join(data_directory_path, "metadata_files", "iso_639_choices.csv")
	iso_languages = read_csv_file(iso_languages_path)
	iso_languages = iso_languages.rename(columns={'name': 'language_name'})

	# Process Digital Humanities terms if required
	if process_dh:
		dh_df_path = os.path.join(data_directory_path, "metadata_files", "en.Digital humanities.json")
		dh_df = pd.DataFrame([json.load(codecs.open(dh_df_path, 'r', 'utf-8-sig'))])
		dh_df = dh_df.melt()
		dh_df.columns = ['language', 'term']
		merged_dh = pd.merge(dh_df, iso_languages, on='language', how='outer')
		merged_dh['term_source'] = 'Digital Humanities'

	# Generate a dataframe with all the terms to translate in all ISO 639-1 languages
	languages_dfs = []
	for term in target_terms:
		term_df = iso_languages.copy()
		term_df['term_source'] = term
		languages_dfs.append(term_df)

	if process_dh:
		languages_dfs.append(merged_dh)

	final_df = pd.concat(languages_dfs).reset_index(drop=True)

	if use_wikipedia:
		# Check if Wikipedia pages exist for the terms
		translations = final_df['term_source'].apply(check_if_wikipedia_page_exists)
		if translations:
			translations_df = pd.DataFrame([translations])
			translations_df = translations_df.T.reset_index().rename(columns={"index": "language_code", 0: "wikipedia_translated_term"})
			final_df = final_df.merge(translations_df, left_on='language', right_on='language_code', how='left')

	# Translate the terms using Google Cloud Translate
	if use_gt_translate:
		if 'wikipedia_translated_term' in final_df.columns:
			grouped_terms = final_df[final_df.wikipedia_translated_term.isna()].groupby(['language', 'language_name']).agg({'term_source': lambda x: list(x)}).reset_index()
		else:
			grouped_terms = final_df.groupby(['language', 'language_name']).agg({'term_source': lambda x: list(x)}).reset_index()
		tqdm.pandas(desc="Translating terms using Google Cloud Translate")
		grouped_terms = grouped_terms.progress_apply(get_gt_translation, axis=1)
		grouped_terms['gt_translated_term'] = grouped_terms['gt_translated_term'].apply(lambda x: [t[1] for t in x] if isinstance(x, list) else x)
		exploded_grouped_gt_terms = grouped_terms.explode(['gt_translated_term', 'term_source'])
		final_df = final_df.merge(exploded_grouped_gt_terms, on=['language', 'language_name', 'term_source'], how='left')

	# Translate the terms using EasyNMT
	if use_enmt_translate:
		if 'wikipedia_translated_term' in final_df.columns:
			grouped_terms = final_df[final_df.wikipedia_translated_term.isna()].groupby(['language', 'language_name']).agg({'term_source': lambda x: list(x)}).reset_index()
		else:
			grouped_terms = final_df.groupby(['language', 'language_name']).agg({'term_source': lambda x: list(x)}).reset_index()
		tqdm.pandas(desc="Translating terms using EasyNMT")
		grouped_terms = grouped_terms.progress_apply(get_enmt_translation, axis=1)
		grouped_terms['enmt_translated_term'] = grouped_terms['enmt_translated_term'].apply(lambda x: [t[1] for t in x] if isinstance(x, list) else x)
		exploded_grouped_enmt_terms = grouped_terms.explode(['enmt_translated_term', 'term_source'])
		final_df = final_df.merge(exploded_grouped_enmt_terms, on=['language', 'language_name', 'term_source'], how='left')

	# Translate the terms using OpenAI
	if use_openai_translate:
		if 'wikipedia_translated_term' in final_df.columns:
			grouped_terms = final_df[final_df.wikipedia_translated_term.isna()].groupby(['language', 'language_name']).agg({'term_source': lambda x: list(x)}).reset_index()
		else:
			grouped_terms = final_df.groupby(['language', 'language_name']).agg({'term_source': lambda x: list(x)}).reset_index()
		tqdm.pandas(desc="Translating terms using OpenAI API")
		grouped_terms = grouped_terms.progress_apply(get_openai_translation, axis=1)
		grouped_terms['openai_translated_term'] = grouped_terms['openai_translated_term'].apply(lambda x: [t[1] for t in x] if isinstance(x, list) else x)
		exploded_grouped_openai_terms = grouped_terms.explode(['openai_translated_term', 'term_source'])
		final_df = final_df.merge(exploded_grouped_openai_terms, on=['language', 'language_name', 'term_source'], how='left')

	cleaned_df = final_df.reset_index(drop=True)

	# Initialize 'term' column if not present
	if 'term' not in cleaned_df.columns:
		cleaned_df['term'] = None


	if use_wikipedia:
		cleaned_df.loc[(cleaned_df.wikipedia_translated_term.notna()) & (cleaned_df.term.isna()), 'term'] = cleaned_df.wikipedia_translated_term
	
	if use_openai_translate:
		cleaned_df.loc[(cleaned_df.openai_translated_term.notna()) & (cleaned_df.term.isna()), 'term'] = cleaned_df.openai_translated_term
	# Use Google Cloud Translate terms if both translations are the same or for German language
	if use_gt_translate:
		cleaned_df.loc[(cleaned_df.gt_translated_term.notna()) & (cleaned_df.term.isna()), 'term'] = cleaned_df.gt_translated_term
		
	if use_enmt_translate:
		cleaned_df.loc[(cleaned_df.term.isna()), 'term'] = cleaned_df.enmt_translated_term

	# Subset to just the terms that were translated
	cleaned_df = cleaned_df[cleaned_df.term.notna()]

	# Ensure we only apply html.unescape to non-None values
	cleaned_df['term'] = cleaned_df['term'].apply(lambda x: html.unescape(x) if x is not None else None)
	cleaned_df['gt_translated_term'] = cleaned_df['gt_translated_term'].apply(lambda x: html.unescape(x) if x is not None else None)
	cleaned_df['enmt_translated_term'] = cleaned_df['enmt_translated_term'].apply(lambda x: html.unescape(x) if x is not None else None)
	cleaned_df['wiki_translated_term'] = cleaned_df['wiki_translated_term'].apply(lambda x: html.unescape(x) if x is not None else None)
	cleaned_df['openai_translated_term'] = cleaned_df['openai_translated_term'].apply(lambda x: html.unescape(x) if x is not None else None)

	if 'code' not in cleaned_df.columns:
		# Rename 'language' column to 'code'
		cleaned_df = cleaned_df.rename(columns={'language': 'code'})

	return cleaned_df

def verify_directionality(grouped_terms_df: pd.DataFrame, grouped_terms_output_path: str, directionality_df: pd.DataFrame) -> pd.DataFrame:
	"""
	Function to verify the directionality of terms

	Parameters
	----------
	grouped_terms_df : pd.DataFrame
		A dataframe with grouped terms
	grouped_terms_output_path : str
		A path to the grouped terms output file
	directionality_df : pd.DataFrame
		A dataframe with language directionality
	Returns a dataframe with verified directionality
	"""
	# Set original index to keep track of the original index
	grouped_terms_df['original_index'] = grouped_terms_df.index
	# Check if there are terms with multiple directionality values
	grouped_terms_df['directionality_counts'] = grouped_terms_df.directionality.str.split(',').str.len()
	# Get terms that need directionality specifications
	needs_directional_specifications = grouped_terms_df[(grouped_terms_df.directionality_counts > 1)]
	# Reset the index
	needs_directional_specifications = needs_directional_specifications.reset_index(drop=True)   
	# Loop through the terms that need directionality specifications    
	for index, row in needs_directional_specifications.iterrows():
		console.print(f"Need to specify directionality for {row.term} in {row['English language name']}. Number {index} out of {len(needs_directional_specifications)}", style="bold blue")
		languages = row['English language name'].split(', ')
		# Get the directionality for the languages
		for direction in ['ltr', 'rtl']:
			console.print(f"Directionality: {direction}", style="bold green")
			total_directionalities = directionality_df[(directionality_df['English language name'].isin(languages)) & (directionality_df.directionality == direction)]
			console.print(f"Total languages with directionality {direction}: {len(total_directionalities)}", style="bold green")
			console.print(f"Languages: {total_directionalities['English language name'].tolist()}", style="bold blue")
		# Get the directionality for the languages and save it to the grouped terms dataframe
		input_directionality = console.input("Enter directionality (ltr or rtl): ")
		grouped_terms_df.loc[row['original_index'], 'directionality'] = input_directionality
		grouped_terms_df.to_csv(f'{grouped_terms_output_path}', index=False)
	# Drop the directionality counts and original index columns
	grouped_terms_df = grouped_terms_df.drop(columns=['directionality_counts'])
	grouped_terms_df = grouped_terms_df.drop(columns=['original_index'])
	# Save the grouped terms dataframe
	grouped_terms_df.to_csv(f'{grouped_terms_output_path}', index=False)
	return grouped_terms_df

def verify_terms(merged_lang_terms_df: pd.DataFrame, processed_translated_terms_output_path: str) -> pd.DataFrame:
	"""
	Function to verify the terms in the grouped terms dataframe

	Parameters
	----------
	merged_lang_terms_df : pd.DataFrame
		A dataframe with merged language terms
	processed_translated_terms_output_path : str
		A path to the processed translated terms output file

	Returns a dataframe with verified terms
	"""
	# Set original index to keep track of the original index
	merged_lang_terms_df['original_index'] = merged_lang_terms_df.index
	# Check if 'keep_term' column exists
	if 'keep_term' not in merged_lang_terms_df.columns:
		merged_lang_terms_df['keep_term'] = True
	# Check if there are terms that need checking
	needs_checking_df = merged_lang_terms_df[(merged_lang_terms_df.wikipedia_translated_term != merged_lang_terms_df.term)]
	# Check for terms that don't agree across all three columns
	needs_checking_df = needs_checking_df[
		(needs_checking_df.gt_translated_term != needs_checking_df.enmt_translated_term) |
		(needs_checking_df.gt_translated_term != needs_checking_df.openai_translated_term) |
		(needs_checking_df.enmt_translated_term != needs_checking_df.openai_translated_term)
	]

	# Reset the index of the resulting DataFrame
	needs_checking_df = needs_checking_df.reset_index(drop=True)
	# Loop through the terms that need checking
	for index, row in needs_checking_df.iterrows():
		original_term = row['term']
		original_gt_term = row['gt_translated_term']
		original_enmt_term = row['enmt_translated_term']
		original_local_name = row['local language name']
		original_openai_term = row['openai_translated_term']

		if row.directionality == 'rtl':
			display_term = get_display(arabic_reshaper.reshape(original_term))
			display_gt_term = get_display(arabic_reshaper.reshape(original_gt_term)) if pd.notna(original_gt_term) else None
			display_enmt_term = get_display(arabic_reshaper.reshape(original_enmt_term)) if pd.notna(original_enmt_term) else None
			display_local_name = get_display(arabic_reshaper.reshape(original_local_name)) if pd.notna(original_local_name) else None
			display_openai_term = get_display(arabic_reshaper.reshape(original_openai_term)) if pd.notna(original_openai_term) else None
		else:
			display_term = original_term
			display_gt_term = original_gt_term
			display_enmt_term = original_enmt_term
			display_local_name = original_local_name
			display_openai_term = original_openai_term

		console.print(f"Current Term: {display_term}. It is {index} out of {len(needs_checking_df)}", style="bold magenta")
		
		if display_openai_term:
			console.print(f"OpenAI Term: {display_openai_term}", style="bold yellow")
		if display_gt_term:
			console.print(f"Google Cloud Translate Term: {display_gt_term}", style="bold blue")
		if display_enmt_term:
			console.print(f"EasyNMT Term: {display_enmt_term}", style="bold white")
		console.print(f"Language: {row['English language name']}", style="bold green")
		if display_local_name:
			console.print(f"Local language name: {display_local_name}", style="bold green")
		console.print(f"Directionality: {row.directionality}", style="bold green")
		console.print(f"Code: {row.code if pd.notna(row.code) else 'None'}", style="bold green")
		console.print(f"Term source: {row.term_source}", style="bold green")
		verified = console.input("Is this term correct? (y/n): ")
		if verified == 'n':
			keep_term = console.input("Do you want to keep this term? (y/n): ")
			if keep_term == 'n':
				merged_lang_terms_df.loc[row.original_index, 'keep_term'] = False
			else:
				new_term = console.input("Enter the correct term: ")
				merged_lang_terms_df.loc[row.original_index, 'term'] = new_term
				merged_lang_terms_df.loc[row.original_index, 'keep_term'] = True
				console.print(f"Updated term: {new_term}", style="bold green")
		else:
			merged_lang_terms_df.loc[row.original_index, 'keep_term'] = True
		merged_lang_terms_df.to_csv(f'{processed_translated_terms_output_path}', index=False)
	merged_lang_terms_df = merged_lang_terms_df.drop(columns=['original_index'])
	merged_lang_terms_df.to_csv(f'{processed_translated_terms_output_path}', index=False)
	return merged_lang_terms_df

def combine_language_data(directionality_df: pd.DataFrame, translated_terms_df: pd.DataFrame, data_directory_path:str) -> Tuple[pd.DataFrame, pd.DataFrame]:
	# Subset directionality to LTR and RTL languages
	directionality_df = directionality_df[directionality_df.directionality.isin(['ltr', 'rtl'])]

	# Merge the directionality data with the translated terms
	merged_lang_terms_df = pd.merge(directionality_df[['code', 'directionality', 'English language name', 'local language name', 'comment', 'local or English Wikipedia article']], translated_terms_df, on='code', how="outer")
	merged_lang_terms_df = merged_lang_terms_df[merged_lang_terms_df.code != "see also Test languages"]

	console.print(f"Our data now contains info for {merged_lang_terms_df[merged_lang_terms_df.term.notna()]['English language name'].nunique()} but we also are missing terms for the following number of languages {merged_lang_terms_df[merged_lang_terms_df.term.isna()]['English language name'].nunique()}", style="bold green")
	merged_lang_terms_df = merged_lang_terms_df[merged_lang_terms_df.term.notna()]
	# Fill NaN values with an empty string
	merged_lang_terms_df['English language name'] = merged_lang_terms_df['English language name'].fillna('').astype(str)
	merged_lang_terms_df['local language name'] = merged_lang_terms_df['local language name'].fillna('').astype(str)
	merged_lang_terms_df['local or English Wikipedia article'] = merged_lang_terms_df['local or English Wikipedia article'].fillna('').astype(str)
	merged_lang_terms_df['comment'] = merged_lang_terms_df['comment'].fillna('').astype(str)
	merged_lang_terms_df = merged_lang_terms_df.reset_index(drop=True)
	processed_translations_dfs = []
	grouped_translations_dfs = []
	for term_source in merged_lang_terms_df.term_source.unique():
		console.print(f"Processing term: {term_source}", style="bold green")
		lower_term = term_source.lower().replace(" ", "_")
		subset_merged_lang_terms_df = merged_lang_terms_df[merged_lang_terms_df.term_source == term_source]
		processed_translated_terms_output_path = os.path.join(data_directory_path, "metadata_files", "translated_terms", lower_term, "processed_translated_terms.csv")
		if os.path.exists(processed_translated_terms_output_path):
			existing_subset_merged_lang_terms_df = read_csv_file(processed_translated_terms_output_path)
			subset_merged_lang_terms_df = pd.concat([subset_merged_lang_terms_df, existing_subset_merged_lang_terms_df])
			subset_merged_lang_terms_df = subset_merged_lang_terms_df.drop_duplicates(subset=['term', 'code'])
		subset_merged_lang_terms_df.to_csv(f'{processed_translated_terms_output_path}', index=False)
		subset_merged_lang_terms_df = subset_merged_lang_terms_df.reset_index(drop=True)
		processed_merged_lang_terms_df = verify_terms(subset_merged_lang_terms_df, processed_translated_terms_output_path)
		processed_translations_dfs.append(processed_merged_lang_terms_df)
		grouped_terms_df = processed_merged_lang_terms_df.groupby(['term_source', 'term']).agg({
			'code': ', '.join,
			'term': 'count',
			'directionality': lambda x: ','.join(set(x.dropna())),
			'English language name': lambda x: ', '.join(x.dropna()),
			'local language name': lambda x: ', '.join(set(x.dropna())),
			'local or English Wikipedia article': lambda x: ', '.join(set(x.dropna())),
			'comment': lambda x: ', '.join(set(x.dropna())),
		}).reset_index(level=0)
		grouped_terms_df = grouped_terms_df.rename(columns={'term': 'counts'})
		grouped_terms_df['term'] = grouped_terms_df.index
		grouped_terms_df = grouped_terms_df.reset_index(drop=True)
		grouped_terms_output_path = os.path.join(data_directory_path, "metadata_files", "translated_terms", lower_term, "grouped_translated_terms.csv")
		if os.path.exists(grouped_terms_output_path):
			existing_grouped_terms_df = read_csv_file(grouped_terms_output_path)
			grouped_terms_df = pd.concat([grouped_terms_df, existing_grouped_terms_df])
			grouped_terms_df = grouped_terms_df.drop_duplicates(subset=['term', 'term_source', 'counts'])
		grouped_terms_df = verify_directionality(grouped_terms_df, grouped_terms_output_path, directionality_df)
		grouped_translations_dfs.append(grouped_terms_df)
	processed_translations_df = pd.concat(processed_translations_dfs)
	grouped_translations_df = pd.concat(grouped_translations_dfs)
	return processed_translations_df, grouped_translations_df

def save_translated_terms(translated_terms_df: pd.DataFrame, updated_target_terms: list, data_directory_path: str) -> None:
	"""
	Save initial translated terms to CSV files for each target term.

	Parameters
	----------
	translated_terms_df : pd.DataFrame
		The DataFrame containing initial translated terms.
	updated_target_terms : list
		A list of target terms to save.
	data_directory_path : str
		The path to the directory where the files will be saved.
	"""
	for term in updated_target_terms:
		lower_term = term.lower().replace(" ", "_")
		translated_terms_output_path = os.path.join(data_directory_path, "metadata_files", "translated_terms", lower_term, "initial_translated_terms.csv")
		subset_translated_terms_df = translated_terms_df[translated_terms_df.term_source == term]
		subset_translated_terms_df.to_csv(translated_terms_output_path, index=False)

def generate_translated_terms(data_directory_path: str, should_rerun_code: bool, target_terms: List, directionality_df: pd.DataFrame, gt_translate: bool, enmt_translate: bool) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
	"""
	Generate translated terms for a list of target terms.

	Parameters
	----------

	data_directory_path : str
		The path to the directory with the datasets.
	should_rerun_code : bool
		A boolean indicating whether to rerun the code.
	target_terms : list
		A list of target terms to translate in all ISO 639-1 languages.
	directionality_df : pd.DataFrame
		A dataframe with language directionality.
	gt_translate : bool
		A boolean indicating whether to use Google Cloud Translate.
	enmt_translate : bool
		A boolean indicating whether to use EasyNMT.
	
	Returns
	-------
	Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
		A tuple with the combined translated, processed, and grouped dataframes.
	"""
	combined_translated_dfs = []
	combined_processed_dfs = []
	combined_grouped_dfs = []
	updated_target_terms = []
	process_dh = False

	for term in target_terms:
		console.print(f"Processing term: {term}", style="bold green")
		lower_term = term.lower().replace(" ", "_")
		translated_terms_output_path = os.path.join(data_directory_path, "metadata_files", "translated_terms", lower_term, "initial_translated_terms.csv")
		process_translated_terms_output_path = os.path.join(data_directory_path, "metadata_files", "translated_terms", lower_term, "processed_translated_terms.csv")
		grouped_translated_terms_output_path = os.path.join(data_directory_path, "metadata_files", "translated_terms", lower_term, "grouped_translated_terms.csv")
		# Load the existing datasets if they exist and rerun_code is False
		if (os.path.exists(translated_terms_output_path)) and (os.path.exists(grouped_translated_terms_output_path)) and (not should_rerun_code) and (os.path.exists(process_translated_terms_output_path)):
			translated_terms_df = read_csv_file(translated_terms_output_path)
			combined_translated_dfs.append(translated_terms_df)
			processed_terms_df = read_csv_file(process_translated_terms_output_path)
			combined_processed_dfs.append(processed_terms_df)
			grouped_terms_df = read_csv_file(grouped_translated_terms_output_path)
			combined_grouped_dfs.append(grouped_terms_df)
		else:
			# Load existing translations if they exist
			if os.path.exists(translated_terms_output_path):
				console.print("Loading existing translated terms", style="bold green")
				translated_terms_df = read_csv_file(translated_terms_output_path)
				combined_translated_dfs.append(translated_terms_df)
			else:
				# If no existing translations, all target terms are considered "missing"
				updated_target_terms.append(term)
	
	if not should_rerun_code:
		process_dh = 'Digital Humanities' in updated_target_terms

		console.print(f"Generating initial terms for {updated_target_terms}", style="bold green")
		if updated_target_terms:
			new_translated_terms_df = generate_initial_terms(updated_target_terms, data_directory_path, process_dh, gt_translate, enmt_translate)
			save_translated_terms(new_translated_terms_df, updated_target_terms, data_directory_path)
			if combined_translated_dfs:
				concat_translated_df = pd.concat(combined_translated_dfs)
				if 'code' not in concat_translated_df.columns and not concat_translated_df.empty:
					concat_translated_df = concat_translated_df.rename(columns={'language': 'code'})
				combined_translated_df = pd.concat([concat_translated_df, new_translated_terms_df]) 
			else: 
				combined_translated_df = new_translated_terms_df

		combined_processed_df, combined_grouped_df = combine_language_data(directionality_df, combined_translated_dfs, data_directory_path)
	else:
		combined_translated_df = pd.concat(combined_translated_dfs)
		combined_processed_df = pd.concat(combined_processed_dfs)
		combined_grouped_df = pd.concat(combined_grouped_dfs)

	return combined_translated_df, combined_processed_df, combined_grouped_df


if __name__ == '__main__':
	local_data_directory_path = get_data_directory_path()
	existing_directionality_path = os.path.join(local_data_directory_path, "metadata_files", "iso_639_choices_directionality_wikimedia.csv")
	local_target_terms: list = ["Digital Humanities"]
	rerun_code = True
	existing_directionality_df = get_directionality(existing_directionality_path)
	gt_translate = True
	enmt_translate = True
	openai_translate = True
	generate_translated_terms(local_data_directory_path, existing_directionality_df, local_target_terms, rerun_code, gt_translate, enmt_translate)