"use client";

import React, { useMemo } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  Node,
  Edge,
  MarkerType,
  BackgroundVariant,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Relationship, Symbol } from "@/types/changestory";
import { Network, Sparkles, ArrowRight } from "lucide-react";

interface ImpactGraphProps {
  changedSymbols: Symbol[];
  affectedSymbols: Symbol[];
  relationships: Relationship[];
  onSelectSymbol: (symbol: Symbol) => void;
  selectedSymbolId?: string | null;
}

export const ImpactGraph: React.FC<ImpactGraphProps> = ({
  changedSymbols,
  affectedSymbols,
  relationships,
  onSelectSymbol,
  selectedSymbolId,
}) => {
  // Build React Flow nodes and edges
  const { nodes, edges } = useMemo(() => {
    const nList: Node[] = [];
    const eList: Edge[] = [];

    // Map symbols by qualified name for quick lookup
    const allSymbolsMap = new Map<string, Symbol>();
    changedSymbols.forEach((s) => allSymbolsMap.set(s.qualified_name, s));
    affectedSymbols.forEach((s) => allSymbolsMap.set(s.qualified_name, s));

    // Layout configuration
    const colWidth = 260;
    const rowHeight = 90;

    // Place changed symbols on the left (or center)
    changedSymbols.forEach((sym, idx) => {
      const isSelected = selectedSymbolId === sym.id;
      nList.push({
        id: sym.qualified_name,
        position: { x: 30, y: 40 + idx * rowHeight },
        data: {
          label: (
            <div
              className={`p-2.5 rounded-lg border text-left transition ${
                isSelected
                  ? "bg-cyan-950 border-cyan-400 shadow-md shadow-cyan-900/60 ring-1 ring-cyan-400"
                  : "bg-slate-900 border-cyan-700/60 hover:border-cyan-500"
              }`}
            >
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400 bg-cyan-950/80 px-1.5 py-0.5 rounded border border-cyan-800">
                  Changed
                </span>
                <span className="text-[10px] font-mono text-slate-500">{sym.type}</span>
              </div>
              <div className="font-mono text-xs font-semibold text-white truncate max-w-[200px]">
                {sym.name}
              </div>
              <div className="text-[10px] text-slate-400 truncate max-w-[200px]">
                {sym.file_path}:{sym.start_line}
              </div>
            </div>
          ),
          rawSymbol: sym,
        },
        style: { width: 220, padding: 0, background: "transparent", border: "none" },
      });
    });

    // Place affected direct callers to the right
    affectedSymbols.forEach((sym, idx) => {
      const isSelected = selectedSymbolId === sym.id;
      nList.push({
        id: sym.qualified_name,
        position: { x: 340, y: 40 + idx * rowHeight },
        data: {
          label: (
            <div
              className={`p-2.5 rounded-lg border text-left transition ${
                isSelected
                  ? "bg-purple-950 border-purple-400 shadow-md shadow-purple-900/60 ring-1 ring-purple-400"
                  : "bg-slate-900 border-purple-700/60 hover:border-purple-500"
              }`}
            >
              <div className="flex items-center justify-between gap-1 mb-1">
                <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 bg-purple-950/80 px-1.5 py-0.5 rounded border border-purple-800">
                  Direct Caller
                </span>
                <span className="text-[10px] font-mono text-slate-500">{sym.type}</span>
              </div>
              <div className="font-mono text-xs font-semibold text-white truncate max-w-[200px]">
                {sym.name}
              </div>
              <div className="text-[10px] text-slate-400 truncate max-w-[200px]">
                {sym.file_path}:{sym.start_line}
              </div>
            </div>
          ),
          rawSymbol: sym,
        },
        style: { width: 220, padding: 0, background: "transparent", border: "none" },
      });
    });

    // Edges from relationship list: caller (source) -> target (callee)
    relationships.forEach((rel, idx) => {
      eList.push({
        id: `rel_${idx}_${rel.source}_${rel.target}`,
        source: rel.source,
        target: rel.target,
        animated: true,
        style: { stroke: "#a855f7", strokeWidth: 2 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: "#a855f7",
          width: 16,
          height: 16,
        },
      });
    });

    return { nodes: nList, edges: eList };
  }, [changedSymbols, affectedSymbols, relationships, selectedSymbolId]);

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-lg flex flex-col h-[480px]">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800">
        <h2 className="text-sm font-semibold text-white flex items-center space-x-2">
          <Network className="h-4 w-4 text-cyan-400" />
          <span>Interactive Impact & Caller Graph</span>
        </h2>
        <div className="flex items-center space-x-4 text-[11px] text-slate-400">
          <span className="flex items-center">
            <span className="h-2 w-2 rounded-full bg-cyan-400 mr-1.5" /> Changed Symbol
          </span>
          <span className="flex items-center">
            <span className="h-2 w-2 rounded-full bg-purple-400 mr-1.5" /> Direct Caller
          </span>
        </div>
      </div>

      <div className="flex-1 w-full relative mt-3 rounded-lg overflow-hidden border border-slate-800/80 bg-slate-950">
        {nodes.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-500 text-xs">
            <Network className="h-8 w-8 mb-2 opacity-30" />
            <span>No symbols detected to graph.</span>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodeClick={(_, node) => {
              if (node.data?.rawSymbol) {
                onSelectSymbol(node.data.rawSymbol as Symbol);
              }
            }}
            fitView
            minZoom={0.5}
            maxZoom={1.5}
          >
            <Background color="#334155" gap={16} variant={BackgroundVariant.Dots} />
            <Controls className="!bg-slate-900 !border-slate-800 !text-white fill-white" />
          </ReactFlow>
        )}
      </div>
    </div>
  );
};
