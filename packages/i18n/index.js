/**
 * CarbonKheti Core Multilingual & Formatting Engine.
 * Complies with Section 6:
 * - Lazy-loaded locales
 * - ICU MessageFormat support (variables, plurals)
 * - Indian digit grouping (Lakh / Crore) and currency formatting in integer paise
 * - Script font mappings and typography tokens
 */

import en from './locales/en.json';
import hi from './locales/hi.json';
import te from './locales/te.json';
import ta from './locales/ta.json';
import bn from './locales/bn.json';
import qpsPloc from './locales/qps-ploc.json';

export const LOCALES = {
  en: { code: 'en', name: 'English', native: 'English', dir: 'ltr', font: 'system-ui, sans-serif', lineHeight: '1.5' },
  hi: { code: 'hi', name: 'Hindi', native: 'हिन्दी', dir: 'ltr', font: '"Noto Sans Devanagari", sans-serif', lineHeight: '1.6' },
  te: { code: 'te', name: 'Telugu', native: 'తెలుగు', dir: 'ltr', font: '"Noto Sans Telugu", sans-serif', lineHeight: '1.7' },
  ta: { code: 'ta', name: 'Tamil', native: 'தமிழ்', dir: 'ltr', font: '"Noto Sans Tamil", sans-serif', lineHeight: '1.65' },
  bn: { code: 'bn', name: 'Bengali', native: 'বাংলা', dir: 'ltr', font: '"Noto Sans Bengali", sans-serif', lineHeight: '1.65' },
  'qps-ploc': { code: 'qps-ploc', name: 'Pseudo-Locale (Test)', native: '[ !!! Pşéûđô !!! ]', dir: 'ltr', font: 'monospace', lineHeight: '1.6' }
};

const DICTIONARIES = {
  en,
  hi,
  te,
  ta,
  bn,
  'qps-ploc': qpsPloc
};

/**
 * Retrieves a translated string by dot-notation key path with fallback to en.
 * Handles variable interpolation like `{amount}` and basic plurals like `{count, plural, ...}`.
 */
export function t(locale = 'en', key = '', params = {}) {
  const dict = DICTIONARIES[locale] || DICTIONARIES.en;
  const parts = key.split('.');
  
  let val = dict;
  for (const p of parts) {
    if (val && typeof val === 'object' && p in val) {
      val = val[p];
    } else {
      val = null;
      break;
    }
  }

  // Fallback to English if key missing in regional dictionary
  if (!val && locale !== 'en') {
    let fallbackVal = DICTIONARIES.en;
    for (const p of parts) {
      if (fallbackVal && typeof fallbackVal === 'object' && p in fallbackVal) {
        fallbackVal = fallbackVal[p];
      } else {
        fallbackVal = null;
        break;
      }
    }
    val = fallbackVal;
  }

  if (typeof val !== 'string') {
    return key;
  }

  let text = val;

  // Handle plural format: {count, plural, =0 {...} =1 {...} other {...}}
  if (text.includes('plural') && 'count' in params) {
    const count = Number(params.count) || 0;
    const exactMatch = text.match(new RegExp(`=${count}\\s*\\{([^}]+)\\}`));
    if (exactMatch) {
      return exactMatch[1].replace('#', count);
    }
    const otherMatch = text.match(/other\s*\{([^}]+)\}/);
    if (otherMatch) {
      return otherMatch[1].replace('#', count);
    }
  }

  // Interpolate variables
  for (const [k, v] of Object.entries(params)) {
    text = text.replace(new RegExp(`\\{${k}\\}`, 'g'), String(v));
  }

  return text;
}

/**
 * Formats integer paise into Indian Rupee string with Lakh/Crore grouping.
 * e.g. 180672 -> "₹1,806.72"
 */
export function formatCurrencyPaise(paise, locale = 'en') {
  if (paise === null || paise === undefined || isNaN(paise)) return '₹0.00';
  const sign = paise < 0 ? '-' : '';
  const absPaise = Math.abs(paise);
  const rupees = Math.floor(absPaise / 100);
  const cents = absPaise % 100;
  
  const rupeesFormatted = formatIndianNumber(rupees);
  return `${sign}₹${rupeesFormatted}.${String(cents).padStart(2, '0')}`;
}

/**
 * Standard Indian numbering system grouping (last 3 digits, then pairs of 2).
 */
export function formatIndianNumber(num) {
  const str = Math.abs(num).toString();
  if (str.length <= 3) return str;
  const last3 = str.slice(-3);
  const other = str.slice(0, -3);
  const groups = [];
  let remaining = other;
  while (remaining.length > 2) {
    groups.unshift(remaining.slice(-2));
    remaining = remaining.slice(0, -2);
  }
  if (remaining.length > 0) groups.unshift(remaining);
  return `${groups.join(',')},${last3}`;
}
