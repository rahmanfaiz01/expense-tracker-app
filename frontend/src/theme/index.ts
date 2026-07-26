import { createTheme } from '@mui/material/styles';
import type { PaletteMode } from '@mui/material';

/** Build an MUI theme for the given color mode. */
export const buildTheme = (mode: PaletteMode) =>
  createTheme({
    palette: {
      mode,
      primary: { main: '#2e7d32' },
      secondary: { main: '#1565c0' },
      ...(mode === 'dark'
        ? { background: { default: '#101418', paper: '#171c22' } }
        : { background: { default: '#f5f7fa' } }),
    },
    shape: { borderRadius: 8 },
    components: {
      MuiCard: { defaultProps: { variant: 'outlined' } },
      MuiPaper: { styleOverrides: { root: { backgroundImage: 'none' } } },
    },
  });

/** Colors used for chart series and category fallbacks. */
export const chartPalette = [
  '#2e7d32',
  '#1565c0',
  '#ef6c00',
  '#6a1b9a',
  '#c62828',
  '#00838f',
  '#9e9d24',
  '#4e342e',
];
