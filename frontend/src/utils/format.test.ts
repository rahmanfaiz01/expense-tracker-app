import { describe, expect, it } from 'vitest';
import { formatCurrency, formatDate, formatMonth } from './format';

describe('formatting helpers', () => {
  it('formats decimal strings as currency without losing cents', () => {
    expect(formatCurrency('1234.50')).toBe('$1,234.50');
    expect(formatCurrency('0.05', 'EUR')).toBe('€0.05');
  });

  it('formats ISO dates in local time', () => {
    expect(formatDate('2026-03-15')).toBe('Mar 15, 2026');
  });

  it('formats report month labels', () => {
    expect(formatMonth('2026-01')).toBe('Jan 26');
  });
});
