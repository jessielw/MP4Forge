import ISO6391 from 'iso-639-1';

export interface Language {
	code: string;
	name: string;
}

// Common languages to show at the top (matching desktop app)
export const COMMON_LANGUAGE_CODES = [
	'en', // English
	'ja', // Japanese
	'es', // Spanish
	'fr', // French
	'de', // German
	'it', // Italian
	'pt', // Portuguese
	'ru', // Russian
	'zh', // Chinese
	'ko', // Korean
	'ar', // Arabic
	'hi'  // Hindi
];

let _languagesCache: Language[] | null = null;
let _commonLanguagesCache: Language[] | null = null;

export function getAllLanguages(): Language[] {
	if (!_languagesCache) {
		_languagesCache = ISO6391.getAllCodes()
			.map(code => ({
				code,
				name: ISO6391.getName(code)
			}))
			.sort((a, b) => a.name.localeCompare(b.name));
	}
	return _languagesCache;
}

export function getCommonLanguages(): Language[] {
	if (!_commonLanguagesCache) {
		const allLangs = getAllLanguages();
		_commonLanguagesCache = COMMON_LANGUAGE_CODES
			.map(code => allLangs.find(lang => lang.code === code))
			.filter((lang): lang is Language => lang !== undefined);
	}
	return _commonLanguagesCache;
}
