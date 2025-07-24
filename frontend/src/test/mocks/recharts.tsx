import React from 'react';
import { vi } from 'vitest';

// Mock all recharts components
export const ResponsiveContainer = ({ children }: any) => <div data-testid="responsive-container">{children}</div>;
export const LineChart = ({ children }: any) => <div data-testid="line-chart">{children}</div>;
export const Line = () => <div data-testid="line" />;
export const AreaChart = ({ children }: any) => <div data-testid="area-chart">{children}</div>;
export const Area = () => <div data-testid="area" />;
export const BarChart = ({ children }: any) => <div data-testid="bar-chart">{children}</div>;
export const Bar = () => <div data-testid="bar" />;
export const RadarChart = ({ children }: any) => <div data-testid="radar-chart">{children}</div>;
export const Radar = () => <div data-testid="radar" />;
export const XAxis = () => <div data-testid="x-axis" />;
export const YAxis = () => <div data-testid="y-axis" />;
export const CartesianGrid = () => <div data-testid="cartesian-grid" />;
export const Tooltip = () => <div data-testid="tooltip" />;
export const Legend = () => <div data-testid="legend" />;
export const ReferenceLine = () => <div data-testid="reference-line" />;
export const PolarGrid = () => <div data-testid="polar-grid" />;
export const PolarAngleAxis = () => <div data-testid="polar-angle-axis" />;
export const PolarRadiusAxis = () => <div data-testid="polar-radius-axis" />;