import AddIcon from '@mui/icons-material/Add';
import DownloadIcon from '@mui/icons-material/Download';
import { Box, Button, Card, CardContent, Stack, TablePagination, Typography } from '@mui/material';
import { useCallback, useEffect, useState } from 'react';
import { listCategories } from '../api/categories';
import { errorMessage } from '../api/client';
import { deleteTransaction, exportTransactionsCsv, listTransactions } from '../api/transactions';
import type { SortOrder, Transaction, TransactionSort } from '../api/types';
import { ConfirmDialog } from '../components/ConfirmDialog';
import { EmptyState, ErrorState, LoadingState } from '../components/StateViews';
import { TransactionFilters } from '../features/transactions/TransactionFilters';
import {
  EMPTY_FILTERS,
  isFiltered,
  toQuery,
  type FilterState,
} from '../features/transactions/filterState';
import { TransactionFormDialog } from '../features/transactions/TransactionFormDialog';
import { TransactionTable } from '../features/transactions/TransactionTable';
import { useApiData } from '../hooks/useApiData';

const PAGE_SIZE_OPTIONS = [10, 25, 50];
const SEARCH_DEBOUNCE_MS = 300;

export const TransactionsPage = () => {
  const [filters, setFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<FilterState>(EMPTY_FILTERS);
  const [sort, setSort] = useState<TransactionSort>('occurred_on');
  const [order, setOrder] = useState<SortOrder>('desc');
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(PAGE_SIZE_OPTIONS[0]);
  const [editing, setEditing] = useState<Transaction | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [pendingDelete, setPendingDelete] = useState<Transaction | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  // Typing in the search box shouldn't fire a request per keystroke.
  useEffect(() => {
    const timer = window.setTimeout(() => {
      setAppliedFilters(filters);
      setPage(0);
    }, SEARCH_DEBOUNCE_MS);
    return () => window.clearTimeout(timer);
  }, [filters]);

  const fetchPage = useCallback(
    () =>
      listTransactions({
        ...toQuery(appliedFilters),
        sort,
        order,
        page: page + 1,
        page_size: pageSize,
      }),
    [appliedFilters, sort, order, page, pageSize],
  );
  const fetchCategories = useCallback(() => listCategories(), []);

  const { data, loading, error, reload } = useApiData(fetchPage);
  const { data: categories } = useApiData(fetchCategories);

  const handleSortChange = (column: TransactionSort) => {
    if (column === sort) {
      setOrder(order === 'asc' ? 'desc' : 'asc');
    } else {
      setSort(column);
      setOrder('desc');
    }
    setPage(0);
  };

  const handleDelete = async () => {
    if (!pendingDelete) {
      return;
    }
    setBusy(true);
    setActionError(null);
    try {
      await deleteTransaction(pendingDelete.id);
      setPendingDelete(null);
      reload();
    } catch (cause) {
      setActionError(errorMessage(cause, 'Unable to delete the transaction'));
    } finally {
      setBusy(false);
    }
  };

  const handleExport = async () => {
    setActionError(null);
    try {
      await exportTransactionsCsv(toQuery(appliedFilters));
    } catch (cause) {
      setActionError(errorMessage(cause, 'Unable to export the transactions'));
    }
  };

  const filtered = isFiltered(appliedFilters);

  return (
    <Stack spacing={3}>
      <Box
        display="flex"
        flexWrap="wrap"
        gap={2}
        alignItems="center"
        justifyContent="space-between"
      >
        <Typography variant="h4" component="h1">
          Transactions
        </Typography>
        <Stack direction="row" spacing={1}>
          <Button
            startIcon={<DownloadIcon />}
            onClick={() => void handleExport()}
            disabled={(data?.total ?? 0) === 0}
          >
            Export CSV
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => {
              setEditing(null);
              setFormOpen(true);
            }}
          >
            Add
          </Button>
        </Stack>
      </Box>

      <Card>
        <CardContent>
          <TransactionFilters
            filters={filters}
            categories={categories ?? []}
            onChange={setFilters}
          />
        </CardContent>
      </Card>

      {actionError ? <ErrorState message={actionError} /> : null}

      <Card>
        {loading ? (
          <LoadingState label="Loading transactions…" />
        ) : error ? (
          <CardContent>
            <ErrorState message={error} onRetry={reload} />
          </CardContent>
        ) : !data || data.items.length === 0 ? (
          <CardContent>
            <EmptyState
              title={filtered ? 'No matching transactions' : 'No transactions yet'}
              description={
                filtered
                  ? 'Try widening the date range or clearing the filters.'
                  : 'Add your first income or expense to get started.'
              }
              action={
                filtered ? (
                  <Button onClick={() => setFilters(EMPTY_FILTERS)}>Clear filters</Button>
                ) : (
                  <Button
                    variant="contained"
                    onClick={() => {
                      setEditing(null);
                      setFormOpen(true);
                    }}
                  >
                    Add a transaction
                  </Button>
                )
              }
            />
          </CardContent>
        ) : (
          <>
            <TransactionTable
              transactions={data.items}
              sort={sort}
              order={order}
              onSortChange={handleSortChange}
              onEdit={(transaction) => {
                setEditing(transaction);
                setFormOpen(true);
              }}
              onDelete={setPendingDelete}
            />
            <TablePagination
              component="div"
              count={data.total}
              page={page}
              onPageChange={(_event, nextPage) => setPage(nextPage)}
              rowsPerPage={pageSize}
              rowsPerPageOptions={PAGE_SIZE_OPTIONS}
              onRowsPerPageChange={(event) => {
                setPageSize(Number(event.target.value));
                setPage(0);
              }}
            />
          </>
        )}
      </Card>

      <TransactionFormDialog
        open={formOpen}
        transaction={editing}
        categories={categories ?? []}
        onClose={() => setFormOpen(false)}
        onSaved={() => {
          setFormOpen(false);
          reload();
        }}
      />

      <ConfirmDialog
        open={pendingDelete !== null}
        title="Delete transaction?"
        description="This permanently removes the entry from your history."
        busy={busy}
        onConfirm={() => void handleDelete()}
        onCancel={() => setPendingDelete(null)}
      />
    </Stack>
  );
};
