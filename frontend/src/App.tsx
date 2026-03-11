import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ProductList from './pages/Products/ProductList';
import ProductDetail from './pages/Products/ProductDetail';
import CategoryTree from './pages/Categories/CategoryTree';
import MediaLibrary from './pages/Media/MediaLibrary';
import QualityDashboard from './pages/Quality/QualityDashboard';
import I18nMissing from './pages/I18n/I18nMissing';
import AttributeFamilies from './pages/Attributes/AttributeFamilies';
import SyncDashboard from './pages/Sync/SyncDashboard';
import QualityRulesAdmin from './pages/Quality/QualityRulesAdmin';
import BrandManager from './pages/Brands/BrandManager';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, refetchOnWindowFocus: false },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              <Route path="/" element={<Dashboard />} />
              <Route path="/products" element={<ProductList />} />
              <Route path="/products/:sku" element={<ProductDetail />} />
              <Route path="/categories" element={<CategoryTree />} />
              <Route path="/media" element={<MediaLibrary />} />
              <Route path="/quality" element={<QualityDashboard />} />
              <Route path="/quality/rules" element={<QualityRulesAdmin />} />
              <Route path="/i18n" element={<I18nMissing />} />
              <Route path="/attributes" element={<AttributeFamilies />} />
              <Route path="/brands" element={<BrandManager />} />
              <Route path="/sync" element={<SyncDashboard />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
