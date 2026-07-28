import CategoryIcon from '@mui/icons-material/Category';
import DarkModeIcon from '@mui/icons-material/DarkMode';
import DashboardIcon from '@mui/icons-material/Dashboard';
import LightModeIcon from '@mui/icons-material/LightMode';
import LogoutIcon from '@mui/icons-material/Logout';
import MenuIcon from '@mui/icons-material/Menu';
import ReceiptLongIcon from '@mui/icons-material/ReceiptLong';
import {
  AppBar,
  Box,
  Container,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { useContext, useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/useAuth';
import { ColorModeContext } from '../theme/ColorModeContext';

const DRAWER_WIDTH = 232;

const NAV_ITEMS = [
  { label: 'Dashboard', to: '/', icon: <DashboardIcon /> },
  { label: 'Transactions', to: '/transactions', icon: <ReceiptLongIcon /> },
  { label: 'Categories', to: '/categories', icon: <CategoryIcon /> },
];

/** Responsive shell: permanent drawer on desktop, temporary drawer on mobile. */
export const AppLayout = () => {
  const theme = useTheme();
  const isDesktop = useMediaQuery(theme.breakpoints.up('md'));
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, logout } = useAuth();
  const { mode, toggleMode } = useContext(ColorModeContext);
  const location = useLocation();

  const navigation = (
    <List>
      {NAV_ITEMS.map((item) => (
        <ListItemButton
          key={item.to}
          component={NavLink}
          to={item.to}
          selected={location.pathname === item.to}
          onClick={() => setMobileOpen(false)}
        >
          <ListItemIcon>{item.icon}</ListItemIcon>
          <ListItemText primary={item.label} />
        </ListItemButton>
      ))}
    </List>
  );

  return (
    <Box display="flex" minHeight="100vh">
      <AppBar position="fixed" sx={{ zIndex: theme.zIndex.drawer + 1 }}>
        <Toolbar>
          {!isDesktop && (
            <IconButton
              color="inherit"
              edge="start"
              aria-label="open navigation"
              onClick={() => setMobileOpen((open) => !open)}
              sx={{ mr: 1 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Expense Tracker
          </Typography>
          {isDesktop && user ? (
            <Typography variant="body2" sx={{ mr: 2 }}>
              {user.email}
            </Typography>
          ) : null}
          <Tooltip title={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}>
            <IconButton color="inherit" onClick={toggleMode} aria-label="toggle dark mode">
              {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Tooltip>
          <Tooltip title="Log out">
            <IconButton color="inherit" onClick={() => void logout()} aria-label="log out">
              <LogoutIcon />
            </IconButton>
          </Tooltip>
        </Toolbar>
      </AppBar>

      <Drawer
        variant={isDesktop ? 'permanent' : 'temporary'}
        open={isDesktop || mobileOpen}
        onClose={() => setMobileOpen(false)}
        ModalProps={{ keepMounted: true }}
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': { width: DRAWER_WIDTH, boxSizing: 'border-box' },
        }}
      >
        <Toolbar />
        <Divider />
        {navigation}
      </Drawer>

      <Box component="main" flexGrow={1} minWidth={0}>
        <Toolbar />
        <Container maxWidth="lg" sx={{ py: 3 }}>
          <Outlet />
        </Container>
      </Box>
    </Box>
  );
};
