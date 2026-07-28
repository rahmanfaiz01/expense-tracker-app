import { CssBaseline, ThemeProvider, useMediaQuery, type PaletteMode } from '@mui/material';
import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import { ColorModeContext } from './ColorModeContext';
import { buildTheme } from './index';

const STORAGE_KEY = 'expense-tracker-color-mode';

const storedMode = (): PaletteMode | null => {
  try {
    const value = window.localStorage.getItem(STORAGE_KEY);
    return value === 'dark' || value === 'light' ? value : null;
  } catch {
    return null; // private mode or storage disabled
  }
};

interface ColorModeProviderProps {
  children: ReactNode;
}

/**
 * Provides the MUI theme and the dark-mode toggle.
 *
 * The chosen mode is a UI preference, so persisting it in localStorage is safe
 * (unlike the access token, which stays in memory).
 */
export const ColorModeProvider = ({ children }: ColorModeProviderProps) => {
  const prefersDark = useMediaQuery('(prefers-color-scheme: dark)');
  const [mode, setMode] = useState<PaletteMode | null>(storedMode);
  const activeMode: PaletteMode = mode ?? (prefersDark ? 'dark' : 'light');

  useEffect(() => {
    if (mode === null) {
      return;
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, mode);
    } catch {
      // ignore: the preference simply won't survive a reload
    }
  }, [mode]);

  const toggleMode = useCallback(
    () => setMode(activeMode === 'dark' ? 'light' : 'dark'),
    [activeMode],
  );

  const value = useMemo(() => ({ mode: activeMode, toggleMode }), [activeMode, toggleMode]);
  const theme = useMemo(() => buildTheme(activeMode), [activeMode]);

  return (
    <ColorModeContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
};
