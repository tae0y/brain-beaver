// refer to https://vaul.emilkowal.ski/default
'use client';

import { Drawer } from 'vaul';

interface VaulDrawerProps {
  title: string;
  keywords: string;
  data_name: string;
  summary: string;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

export default function VaulDrawer({
    title,
    keywords,
    data_name,
    summary,
    isOpen,
    onOpenChange,
}: VaulDrawerProps) {
  return (
    <Drawer.Root open={isOpen} onOpenChange={onOpenChange}>
      <Drawer.Portal>
      <Drawer.Overlay className="drawer-overlay" />
        <Drawer.Content className="drawer-content">
          <div className="drawer-handle" aria-hidden />
          <Drawer.Title className="drawer-title">{title}</Drawer.Title>
          <p>Keywords: {keywords}</p>
          <p>Data Name: {data_name}</p>
          <p>Summary: {summary}</p>
        </Drawer.Content>
      </Drawer.Portal>
    </Drawer.Root>
  );
}