import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import {
  Chip,
  IconButton,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Typography,
} from '@mui/material';
import type { SortOrder, Transaction, TransactionSort } from '../../api/types';
import { formatCurrency, formatDate } from '../../utils/format';

interface Column {
  id: TransactionSort | 'category' | 'actions';
  label: string;
  sortable: boolean;
  numeric?: boolean;
}

const COLUMNS: Column[] = [
  { id: 'occurred_on', label: 'Date', sortable: true },
  { id: 'description', label: 'Description', sortable: true },
  { id: 'category', label: 'Category', sortable: false },
  { id: 'amount', label: 'Amount', sortable: true, numeric: true },
  { id: 'actions', label: '', sortable: false },
];

interface TransactionTableProps {
  transactions: Transaction[];
  sort: TransactionSort;
  order: SortOrder;
  onSortChange: (sort: TransactionSort) => void;
  onEdit: (transaction: Transaction) => void;
  onDelete: (transaction: Transaction) => void;
}

export const TransactionTable = ({
  transactions,
  sort,
  order,
  onSortChange,
  onEdit,
  onDelete,
}: TransactionTableProps) => (
  <TableContainer>
    <Table size="small">
      <TableHead>
        <TableRow>
          {COLUMNS.map((column) => (
            <TableCell key={column.id} align={column.numeric ? 'right' : 'left'}>
              {column.sortable ? (
                <TableSortLabel
                  active={sort === column.id}
                  direction={sort === column.id ? order : 'desc'}
                  onClick={() => onSortChange(column.id as TransactionSort)}
                >
                  {column.label}
                </TableSortLabel>
              ) : (
                column.label
              )}
            </TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {transactions.map((transaction) => (
          <TableRow key={transaction.id} hover>
            <TableCell>{formatDate(transaction.occurred_on)}</TableCell>
            <TableCell>
              {transaction.description ?? (
                <Typography variant="body2" color="text.secondary">
                  —
                </Typography>
              )}
            </TableCell>
            <TableCell>
              <Chip
                size="small"
                label={transaction.category_name ?? 'Uncategorized'}
                variant={transaction.category_name ? 'filled' : 'outlined'}
              />
            </TableCell>
            <TableCell align="right">
              <Typography
                variant="body2"
                color={transaction.type === 'income' ? 'success.main' : 'error.main'}
                fontWeight={600}
              >
                {transaction.type === 'income' ? '+' : '−'}
                {formatCurrency(transaction.amount, transaction.currency)}
              </Typography>
            </TableCell>
            <TableCell align="right">
              <IconButton
                size="small"
                aria-label={`edit ${transaction.description ?? 'transaction'}`}
                onClick={() => onEdit(transaction)}
              >
                <EditIcon fontSize="small" />
              </IconButton>
              <IconButton
                size="small"
                aria-label={`delete ${transaction.description ?? 'transaction'}`}
                onClick={() => onDelete(transaction)}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
);
