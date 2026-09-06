"use client";

import React, { createContext, useContext, useMemo, useState } from "react";
import { DataMode } from "@/design-system/tokens";

export interface OperationalState {
  dataMode: DataMode;
  activeRegion: string;
}

export interface OperationalContextType extends OperationalState {
  setDataMode: (mode: DataMode) => void;
  setActiveRegion: (region: string) => void;
}

const defaultOperationalContext: OperationalContextType = {
  dataMode:
    (process.env.NEXT_PUBLIC_DATA_MODE as DataMode) || "demo",
  activeRegion:
    process.env.NEXT_PUBLIC_ACTIVE_REGION || "himalayan_pilot",
  setDataMode: () => {},
  setActiveRegion: () => {},
};

export const OperationalContext = createContext<OperationalContextType>(
  defaultOperationalContext
);

export interface OperationalProviderProps {
  children: React.ReactNode;
  initialState?: Partial<OperationalState>;
}

export const OperationalProvider: React.FC<OperationalProviderProps> = ({
  children,
  initialState,
}) => {
  const [dataMode, setDataMode] = useState<DataMode>(
    initialState?.dataMode ??
      (process.env.NEXT_PUBLIC_DATA_MODE as DataMode) ??
      "demo"
  );
  const [activeRegion, setActiveRegion] = useState<string>(
    initialState?.activeRegion ??
      process.env.NEXT_PUBLIC_ACTIVE_REGION ??
      "himalayan_pilot"
  );

  const value = useMemo<OperationalContextType>(
    () => ({
      dataMode,
      activeRegion,
      setDataMode,
      setActiveRegion,
    }),
    [dataMode, activeRegion]
  );

  return (
    <OperationalContext.Provider value={value}>
      {children}
    </OperationalContext.Provider>
  );
};

export function useOperational(): OperationalContextType {
  return useContext(OperationalContext);
}
