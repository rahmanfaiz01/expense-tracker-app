import {
  Alert,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
} from '@mui/material';
import { useEffect, useState, type FormEvent } from 'react';
import { createCategory, updateCategory } from '../../api/categories';
import { errorMessage } from '../../api/client';
import type { Category, TransactionType } from '../../api/types';

const DEFAULT_COLOR = '#2E7D32';

interface CategoryFormDialogProps {
  open: boolean;
  category: Category | null;
  onClose: () => void;
  onSaved: () => void;
}

export const CategoryFormDialog = ({
  open,
  category,
  onClose,
  onSaved,
}: CategoryFormDialogProps) => {
  const [name, setName] = useState('');
  const [type, setType] = useState<TransactionType>('expense');
  const [color, setColor] = useState(DEFAULT_COLOR);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setName(category?.name ?? '');
      setType(category?.type ?? 'expense');
      setColor(category?.color ?? DEFAULT_COLOR);
      setError(null);
    }
  }, [open, category]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSaving(true);
    const payload = { name: name.trim(), type, color };
    try {
      if (category) {
        await updateCategory(category.id, payload);
      } else {
        await createCategory(payload);
      }
      onSaved();
    } catch (cause) {
      setError(errorMessage(cause, 'Unable to save the category'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <form onSubmit={(event) => void handleSubmit(event)} noValidate>
        <DialogTitle>{category ? 'Edit category' : 'Add category'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            {error ? <Alert severity="error">{error}</Alert> : null}
            <TextField
              label="Name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              inputProps={{ maxLength: 100 }}
              required
              fullWidth
            />
            <TextField
              select
              label="Type"
              value={type}
              onChange={(event) => setType(event.target.value as TransactionType)}
              fullWidth
            >
              <MenuItem value="expense">Expense</MenuItem>
              <MenuItem value="income">Income</MenuItem>
            </TextField>
            <TextField
              label="Color"
              type="color"
              value={color}
              onChange={(event) => setColor(event.target.value)}
              InputLabelProps={{ shrink: true }}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={saving || !name.trim()}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};
