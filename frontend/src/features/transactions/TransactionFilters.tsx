import { Button, Grid, MenuItem, TextField } from '@mui/material';
import type { Category, TransactionType } from '../../api/types';
import { EMPTY_FILTERS, isFiltered, type FilterState } from './filterState';

interface TransactionFiltersProps {
  filters: FilterState;
  categories: Category[];
  onChange: (filters: FilterState) => void;
}

export const TransactionFilters = ({ filters, categories, onChange }: TransactionFiltersProps) => {
  const update = (patch: Partial<FilterState>) => onChange({ ...filters, ...patch });

  return (
    <Grid container spacing={2} alignItems="center">
      <Grid item xs={12} md={3}>
        <TextField
          label="Search description"
          value={filters.q}
          onChange={(event) => update({ q: event.target.value })}
          size="small"
          fullWidth
        />
      </Grid>
      <Grid item xs={6} md={2}>
        <TextField
          select
          label="Type"
          value={filters.type}
          onChange={(event) => update({ type: event.target.value as TransactionType | '' })}
          size="small"
          fullWidth
        >
          <MenuItem value="">All</MenuItem>
          <MenuItem value="income">Income</MenuItem>
          <MenuItem value="expense">Expense</MenuItem>
        </TextField>
      </Grid>
      <Grid item xs={6} md={3}>
        <TextField
          select
          label="Category"
          value={filters.categoryId}
          onChange={(event) => update({ categoryId: event.target.value })}
          size="small"
          fullWidth
        >
          <MenuItem value="">All</MenuItem>
          {categories.map((category) => (
            <MenuItem key={category.id} value={category.id}>
              {category.name}
            </MenuItem>
          ))}
        </TextField>
      </Grid>
      <Grid item xs={6} md={2}>
        <TextField
          label="From"
          type="date"
          value={filters.dateFrom}
          onChange={(event) => update({ dateFrom: event.target.value })}
          InputLabelProps={{ shrink: true }}
          size="small"
          fullWidth
        />
      </Grid>
      <Grid item xs={6} md={2}>
        <TextField
          label="To"
          type="date"
          value={filters.dateTo}
          onChange={(event) => update({ dateTo: event.target.value })}
          InputLabelProps={{ shrink: true }}
          size="small"
          fullWidth
        />
      </Grid>
      {isFiltered(filters) ? (
        <Grid item xs={12}>
          <Button size="small" onClick={() => onChange(EMPTY_FILTERS)}>
            Clear filters
          </Button>
        </Grid>
      ) : null}
    </Grid>
  );
};
