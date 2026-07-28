import { createContext } from 'react';
import type { PaletteMode } from '@mui/material';

export interface ColorModeValue {
  mode: PaletteMode;
  toggleMode: () => void;
}

export const ColorModeContext = createContext<ColorModeValue>({
  mode: 'light',
  toggleMode: () => undefined,
});
