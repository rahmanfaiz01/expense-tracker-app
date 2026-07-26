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
import { errorMessage } from '../../api/client';
import { createTransaction, updateTransaction } from '../../api/transactions';
import type { Category, Transaction, TransactionInput, TransactionType } from '../../api/types';
import { today } from '../../utils/format';

interface FormState {
  type: TransactionType;
  amount: string;
  occurredOn: string;
  description: string;
  categoryId: string;
  currency: string;
}

const emptyForm = (): FormState => ({
  type: 'expense',
  amount: '',
  occurredOn: today(),
  description: '',
  categoryId: '',
  currency: 'USD',
});

const fromTransaction = (transaction: Transaction): FormState => ({
  type: transaction.type,
  amount: transaction.amount,
  occurredOn: transaction.occurred_on,
  description: transaction.description ?? '',
  categoryId: transaction.category_id ?? '',
  currency: transaction.currency,
});

interface TransactionFormDialogProps {
  open: boolean;
  transaction: Transaction | null;
  categories: Category[];
  onClose: () => void;
  onSaved: () => void;
}

export const TransactionFormDialog = ({
  open,
  transaction,
  categories,
  onClose,
  onSaved,
}: TransactionFormDialogProps) => {
  const [form, setForm] = useState<FormState>(emptyForm);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (open) {
      setForm(transaction ? fromTransaction(transaction) : emptyForm());
      setError(null);
    }
  }, [open, transaction]);

  // Only categories of the selected type can be attached to the entry.
  const selectable = categories.filter((category) => category.type === form.type);

  const update = (patch: Partial<FormState>) => setForm((current) => ({ ...current, ...patch }));

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSaving(true);
    const payload: TransactionInput = {
      type: form.type,
      amount: form.amount,
      currency: form.currency,
      description: form.description.trim() || null,
      occurred_on: form.occurredOn,
      category_id: form.categoryId || null,
    };
    try {
      if (transaction) {
        await updateTransaction(transaction.id, payload);
      } else {
        await createTransaction(payload);
      }
      onSaved();
    } catch (cause) {
      setError(errorMessage(cause, 'Unable to save the transaction'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={(event) => void handleSubmit(event)} noValidate>
        <DialogTitle>{transaction ? 'Edit transaction' : 'Add transaction'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            {error ? <Alert severity="error">{error}</Alert> : null}
            <TextField
              select
              label="Type"
              value={form.type}
              onChange={(event) =>
                update({ type: event.target.value as TransactionType, categoryId: '' })
              }
              fullWidth
            >
              <MenuItem value="expense">Expense</MenuItem>
              <MenuItem value="income">Income</MenuItem>
            </TextField>
            <TextField
              label="Amount"
              type="number"
              value={form.amount}
              onChange={(event) => update({ amount: event.target.value })}
              inputProps={{ step: '0.01', min: '0.01' }}
              required
              fullWidth
            />
            <TextField
              label="Date"
              type="date"
              value={form.occurredOn}
              onChange={(event) => update({ occurredOn: event.target.value })}
              InputLabelProps={{ shrink: true }}
              required
              fullWidth
            />
            <TextField
              select
              label="Category"
              value={form.categoryId}
              onChange={(event) => update({ categoryId: event.target.value })}
              helperText={
                selectable.length === 0 ? `No ${form.type} categories yet — optional` : undefined
              }
              fullWidth
            >
              <MenuItem value="">Uncategorized</MenuItem>
              {selectable.map((category) => (
                <MenuItem key={category.id} value={category.id}>
                  {category.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="Description"
              value={form.description}
              onChange={(event) => update({ description: event.target.value })}
              inputProps={{ maxLength: 255 }}
              fullWidth
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button type="submit" variant="contained" disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};
