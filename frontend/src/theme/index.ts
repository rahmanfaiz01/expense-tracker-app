import { createTheme } from '@mui/material/styles';
import type { PaletteMode } from '@mui/material';

/**
 * Build an MUI theme for the given color mode.
 *
 * Dark mode is fully wired up in a later phase; the light/dark palettes are
 * defined here so the toggle can be added without restructuring the theme.
 */
export const buildTheme = (mode: PaletteMode) =>
  createTheme({
    palette: {
      mode,
      primary: { main: '#2e7d32' },
      secondary: { main: '#1565c0' },
    },
    shape: { borderRadius: 8 },
  });
