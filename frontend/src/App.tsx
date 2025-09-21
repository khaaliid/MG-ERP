import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LedgerToday from './pages/LedgerToday';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LedgerToday />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
