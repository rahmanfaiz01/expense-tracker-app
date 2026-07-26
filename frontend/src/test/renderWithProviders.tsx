import { render, type RenderResult } from '@testing-library/react';
import type { ReactElement } from 'react';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../auth/AuthProvider';
import { ColorModeProvider } from '../theme/ColorModeProvider';

interface Options {
  route?: string;
  withAuth?: boolean;
}

/** Render a component inside the providers the app supplies at runtime. */
export const renderWithProviders = (
  ui: ReactElement,
  { route = '/', withAuth = true }: Options = {},
): RenderResult => {
  const tree = (
    <ColorModeProvider>
      <MemoryRouter initialEntries={[route]}>
        {withAuth ? <AuthProvider>{ui}</AuthProvider> : ui}
      </MemoryRouter>
    </ColorModeProvider>
  );
  return render(tree);
};
