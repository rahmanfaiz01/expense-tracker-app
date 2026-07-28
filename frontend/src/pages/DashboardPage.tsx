import { Box, Button, Card, CardContent, Grid, Stack, Typography } from '@mui/material';
import { useCallback } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { fetchByCategory, fetchMonthly, fetchSummary } from '../api/reports';
import type { CategoryTotal, MonthlyPoint, Summary } from '../api/types';
import { EmptyState, ErrorState, LoadingState } from '../components/StateViews';
import { CategoryChart } from '../features/dashboard/CategoryChart';
import { MonthlyChart } from '../features/dashboard/MonthlyChart';
import { SummaryCards } from '../features/dashboard/SummaryCards';
import { useApiData } from '../hooks/useApiData';

const MONTHS = 6;

interface DashboardData {
  summary: Summary;
  monthly: MonthlyPoint[];
  byCategory: CategoryTotal[];
}

export const DashboardPage = () => {
  const fetcher = useCallback(async (): Promise<DashboardData> => {
    const [summary, monthly, byCategory] = await Promise.all([
      fetchSummary(),
      fetchMonthly(MONTHS),
      fetchByCategory('expense'),
    ]);
    return { summary, monthly, byCategory };
  }, []);

  const { data, loading, error, reload } = useApiData(fetcher);

  if (loading) {
    return <LoadingState label="Loading your dashboard…" />;
  }
  if (error) {
    return <ErrorState message={error} onRetry={reload} />;
  }
  if (!data) {
    return null;
  }

  const hasTransactions = data.summary.transaction_count > 0;

  return (
    <Stack spacing={3}>
      <Box>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {data.summary.transaction_count} transaction
          {data.summary.transaction_count === 1 ? '' : 's'} recorded
        </Typography>
      </Box>

      <SummaryCards summary={data.summary} />

      {!hasTransactions ? (
        <Card>
          <CardContent>
            <EmptyState
              title="No transactions yet"
              description="Add your first income or expense to see charts and totals here."
              action={
                <Button component={RouterLink} to="/transactions" variant="contained">
                  Add a transaction
                </Button>
              }
            />
          </CardContent>
        </Card>
      ) : (
        <Grid container spacing={2}>
          <Grid item xs={12} md={7}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Income vs expenses
                </Typography>
                <MonthlyChart data={data.monthly} />
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={5}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Expenses by category
                </Typography>
                {data.byCategory.length === 0 ? (
                  <EmptyState
                    title="No expenses yet"
                    description="Expense totals appear here once you record one."
                  />
                ) : (
                  <CategoryChart data={data.byCategory} />
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Stack>
  );
};
