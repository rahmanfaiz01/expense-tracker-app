/** Formatting helpers shared by the dashboard, tables and charts. */

export const formatCurrency = (amount: string | number, currency = 'USD'): string =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(Number(amount));

export const formatDate = (isoDate: string): string =>
  new Date(`${isoDate}T00:00:00`).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  });

/** Turn a `YYYY-MM` report label into a short chart label such as `Mar 26`. */
export const formatMonth = (month: string): string => {
  const [year, monthPart] = month.split('-');
  const date = new Date(Number(year), Number(monthPart) - 1, 1);
  return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
};

/** Today's date as `YYYY-MM-DD`, using local time rather than UTC. */
export const today = (): string => {
  const now = new Date();
  const month = `${now.getMonth() + 1}`.padStart(2, '0');
  const day = `${now.getDate()}`.padStart(2, '0');
  return `${now.getFullYear()}-${month}-${day}`;
};
