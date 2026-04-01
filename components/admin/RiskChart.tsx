"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";

const data = [
  { name: "High Risk", value: 35, color: "#818cf8" }, // indigo-400
  { name: "Medium Risk", value: 25, color: "#fb923c" }, // orange-400
  { name: "Authentic", value: 40, color: "#4ade80" }, // green-400
];

export function RiskChart() {
  return (
    <div className="w-full h-full relative">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={75}
            paddingAngle={5}
            dataKey="value"
            stroke="rgba(255,255,255,0.05)"
            strokeWidth={2}
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
            itemStyle={{ color: '#fff', fontSize: '13px', fontWeight: 600 }}
          />
        </PieChart>
      </ResponsiveContainer>
      
      {/* Center Label */}
      <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
        <span className="text-[24px] font-heading font-bold text-white leading-none">2.4k</span>
        <span className="text-[10px] text-slate-400 uppercase tracking-widest mt-1">Total Flags</span>
      </div>
    </div>
  );
}
