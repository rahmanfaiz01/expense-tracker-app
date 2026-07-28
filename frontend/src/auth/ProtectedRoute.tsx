import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { FullPageLoader } from '../components/FullPageLoader';
import { useAuth } from './useAuth';

/** Gate for authenticated pages; remembers where the user was heading. */
export const ProtectedRoute = () => {
  const { status } = useAuth();
  const location = useLocation();

  if (status === 'loading') {
    return <FullPageLoader label="Restoring your session…" />;
  }
  if (status === 'anonymous') {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return <Outlet />;
};

/** Keeps signed-in users away from the login and registration pages. */
export const PublicOnlyRoute = () => {
  const { status } = useAuth();

  if (status === 'loading') {
    return <FullPageLoader label="Loading…" />;
  }
  if (status === 'authenticated') {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
};
