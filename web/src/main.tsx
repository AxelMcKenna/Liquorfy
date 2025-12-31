import React, { lazy, Suspense } from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { LocationProvider } from "@/contexts/LocationContext";
import { CompareProvider } from "@/contexts/CompareContext";
import { Toaster } from "sonner";
import "maplibre-gl/dist/maplibre-gl.css";
import "./styles.css";

// Lazy load route components for code splitting
const Landing = lazy(() => import("@/pages/Landing"));
const Explore = lazy(() => import("@/pages/Explore"));
const ProductDetail = lazy(() => import("@/pages/ProductDetail"));

// Loading fallback component
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center bg-white">
    <div className="text-center">
      <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
      <p className="text-gray-600">Loading...</p>
    </div>
  </div>
);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <LocationProvider>
        <CompareProvider>
          <Toaster position="top-right" richColors closeButton />
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/explore" element={<Explore />} />
              <Route path="/product/:id" element={<ProductDetail />} />
            </Routes>
          </Suspense>
        </CompareProvider>
      </LocationProvider>
    </BrowserRouter>
  </React.StrictMode>
);
