import { createRoot } from 'react-dom/client';
import DataManagementPanel from './admin';
import './admin-style.css';

const container = document.getElementById('admin-root')!;
const root = createRoot(container);

root.render(<DataManagementPanel />);