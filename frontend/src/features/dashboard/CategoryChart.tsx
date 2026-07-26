import { useTheme } from '@mui/material';
import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import type { CategoryTotal } from '../../api/types';
import { chartPalette } from '../../theme';
import { formatCurrency } from '../../utils/format';

interface CategoryChartProps {
  data: CategoryTotal[];
}

/** Expense totals per category; each slice uses the category color when set. */
export const CategoryChart = ({ data }: CategoryChartProps) => {
  const theme = useTheme();
  const slices = data.map((row, index) => ({
    name: row.category_name,
    value: Number(row.total),
    color: row.color ?? chartPalette[index % chartPalette.length],
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie data={slices} dataKey="value" nameKey="name" innerRadius={55} outerRadius={95}>
          {slices.map((slice) => (
            <Cell key={slice.name} fill={slice.color} stroke={theme.palette.background.paper} />
          ))}
        </Pie>
        <Tooltip
          formatter={(value: number) => formatCurrency(value)}
          contentStyle={{
            background: theme.palette.background.paper,
            border: `1px solid ${theme.palette.divider}`,
            color: theme.palette.text.primary,
          }}
        />
        <Legend />
      </PieChart>
    </ResponsiveContainer>
  );
};
