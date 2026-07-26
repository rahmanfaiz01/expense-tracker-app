import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  IconButton,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useCallback, useState } from 'react';
import { deleteCategory, listCategories } from '../api/categories';
import { errorMessage } from '../api/client';
import type { Category } from '../api/types';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { EmptyState, ErrorState, LoadingState } from '../components/StateViews';
import { CategoryFormDialog } from '../features/categories/CategoryFormDialog';
import { useApiData } from '../hooks/useApiData';

export const CategoriesPage = () => {
  const fetchCategories = useCallback(() => listCategories(), []);
  const { data, loading, error, reload } = useApiData(fetchCategories);
  const [editing, setEditing] = useState<Category | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Category | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const openCreate = () => {
    setEditing(null);
    setFormOpen(true);
  };

  const handleDelete = async () => {
    if (!pendingDelete) {
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      await deleteCategory(pendingDelete.id);
      setPendingDelete(null);
      reload();
    } catch (cause) {
      setActionError(errorMessage(cause, 'Unable to delete the category'));
    } finally {
      setBusy(false);
    }
  };

  return (
    <Stack spacing={3}>
      <Box display="flex" alignItems="center" justifyContent="space-between" gap={2}>
        <Typography variant="h4" component="h1">
          Categories
        </Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={openCreate}>
          Add
        </Button>
      </Box>

      {actionError ? <ErrorState message={actionError} /> : null}

      <Card>
        {loading ? (
          <LoadingState label="Loading categories…" />
        ) : error ? (
          <CardContent>
            <ErrorState message={error} onRetry={reload} />
          </CardContent>
        ) : !data || data.length === 0 ? (
          <CardContent>
            <EmptyState
              title="No categories yet"
              description="Categories group your transactions and power the dashboard breakdown."
              action={
                <Button variant="contained" onClick={openCreate}>
                  Add a category
                </Button>
              }
            />
          </CardContent>
        ) : (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Type</TableCell>
                  <TableCell>Color</TableCell>
                  <TableCell align="right" />
                </TableRow>
              </TableHead>
              <TableBody>
                {data.map((category) => (
                  <TableRow key={category.id} hover>
                    <TableCell>{category.name}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={category.type}
                        color={category.type === 'income' ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Box
                          sx={{
                            width: 16,
                            height: 16,
                            borderRadius: '50%',
                            bgcolor: category.color ?? 'action.disabled',
                            border: '1px solid',
                            borderColor: 'divider',
                          }}
                        />
                        <Typography variant="body2" color="text.secondary">
                          {category.color ?? '—'}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <IconButton
                        size="small"
                        aria-label={`edit ${category.name}`}
                        onClick={() => {
                          setEditing(category);
                          setFormOpen(true);
                        }}
                      >
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton
                        size="small"
                        aria-label={`delete ${category.name}`}
                        onClick={() => setPendingDelete(category)}
                      >
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Card>

      <CategoryFormDialog
        open={formOpen}
        category={editing}
        onClose={() => setFormOpen(false)}
        onSaved={() => {
          setFormOpen(false);
          reload();
        }}
      />

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete category?"
        description="Transactions in this category are kept and become uncategorized."
        busy={busy}
        onConfirm={() => void handleDelete()}
        onCancel={() => setPendingDelete(null)}
      />
    </Stack>
  );
};
