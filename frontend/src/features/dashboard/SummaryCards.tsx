import { Card, CardContent, Grid, Typography } from '@mui/material';
import type { Summary } from '../../api/types';
import { formatCurrency } from '../../utils/format';

interface SummaryCardsProps {
  summary: Summary;
}

export const SummaryCards = ({ summary }: SummaryCardsProps) => {
  const balance = Number(summary.balance);
  const cards = [
    { label: 'Total income', value: summary.total_income, color: 'success.main' },
    { label: 'Total expenses', value: summary.total_expenses, color: 'error.main' },
    {
      label: 'Balance',
      value: summary.balance,
      color: balance < 0 ? 'error.main' : 'text.primary',
    },
  ];

  return (
    <Grid container spacing={2}>
      {cards.map((card) => (
        <Grid item xs={12} sm={4} key={card.label}>
          <Card>
            <CardContent>
              <Typography variant="overline" color="text.secondary">
                {card.label}
              </Typography>
              <Typography variant="h5" color={card.color} sx={{ wordBreak: 'break-word' }}>
                {formatCurrency(card.value)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};
