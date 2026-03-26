import { PriceHistoryPoint } from '@/types';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

interface Props {
  history: PriceHistoryPoint[];
}

const formatDate = (dateStr: string) => {
  const d = new Date(dateStr + 'T00:00:00');
  return d.toLocaleDateString('en-NZ', { month: 'short', day: 'numeric' });
};

const formatPrice = (value: number) => `$${value.toFixed(2)}`;

interface ChartPoint {
  date: string;
  label: string;
  price: number;
}

export const PriceHistoryChart = ({ history }: Props) => {
  const data: ChartPoint[] = history.map((p) => ({
    date: p.date,
    label: formatDate(p.date),
    price: p.promo_price_nzd != null ? Math.min(p.promo_price_nzd, p.price_nzd) : p.price_nzd,
  }));

  const prices = data.map((d) => d.price);
  const minPrice = Math.min(...prices);
  const maxPrice = Math.max(...prices);
  const padding = (maxPrice - minPrice) * 0.15 || 1;

  return (
    <div className="w-full h-52 md:h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: -8 }}>
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.2} />
              <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 11, fill: 'hsl(var(--foreground-secondary))' }}
            tickLine={false}
            axisLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            domain={[minPrice - padding, maxPrice + padding]}
            tickFormatter={formatPrice}
            tick={{ fontSize: 11, fill: 'hsl(var(--foreground-secondary))' }}
            tickLine={false}
            axisLine={false}
            width={56}
          />
          <Tooltip
            formatter={(value) => [formatPrice(Number(value)), 'Price']}
            labelFormatter={(label) => String(label)}
            contentStyle={{
              borderRadius: '8px',
              border: '1px solid hsl(var(--border))',
              fontSize: '13px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
            }}
          />
          <Area
            type="monotone"
            dataKey="price"
            stroke="hsl(var(--primary))"
            strokeWidth={2}
            fill="url(#priceGradient)"
            dot={false}
            activeDot={{ r: 4, fill: 'hsl(var(--primary))' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
