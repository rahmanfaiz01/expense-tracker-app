import { useTheme } from '@mui/material';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { MonthlyPoint } from '../../api/types';
import { formatCurrency, formatMonth } from '../../utils/format';

interface MonthlyChartProps {
  data: MonthlyPoint[];
}

/** Income vs expenses per month. */
export const MonthlyChart = ({ data }: MonthlyChartProps) => {
  const theme = useTheme();
  const points = data.map((point) => ({
    month: formatMonth(point.month),
    income: Number(point.income),
    expenses: Number(point.expenses),
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={points} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
        <XAxis dataKey="month" stroke={theme.palette.text.secondary} fontSize={12} />
        <YAxis stroke={theme.palette.text.secondary} fontSize={12} width={70} />
        <Tooltip
          formatter={(value: number) => formatCurrency(value)}
          contentStyle={{
            background: theme.palette.background.paper,
            border: `1px solid ${theme.palette.divider}`,
            color: theme.palette.text.primary,
          }}
        />
        <Legend />
        <Bar
          dataKey="income"
          name="Income"
          fill={theme.palette.success.main}
          radius={[4, 4, 0, 0]}
        />
        <Bar
          dataKey="expenses"
          name="Expenses"
          fill={theme.palette.error.main}
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
};
