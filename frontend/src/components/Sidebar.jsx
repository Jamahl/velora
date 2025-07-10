import React from "react";
import { Link, useLocation } from "react-router-dom";

const navItems = [
  { label: "Wishlist Board", to: "/" },
  { label: "Find Similar Products", to: "/similar-products" },
  { label: "Find Similar Products V2", to: "/find-similar-products-v2" },
];

export default function Sidebar() {
  const location = useLocation();
  return (
    <aside className="h-screen w-56 bg-black border-r border-gray-800 flex flex-col p-4 fixed left-0 top-0 z-20 shadow-xl">
      <div className="flex flex-col items-center gap-2 mb-8 mt-2">
        <div className="relative">
          <div className="bg-white text-black rounded-full w-16 h-16 flex items-center justify-center text-2xl font-bold shadow-lg">
            V
          </div>
        </div>
        <span className="font-extrabold text-xl text-white">Velora2</span>
      </div>
      <nav aria-label="Main navigation" className="flex flex-col gap-2 mt-4">
        {navItems.map((item) => (
          <Link
            key={item.to}
            to={item.to}
            className={`flex items-center justify-start text-lg px-4 py-2 transition-all duration-150 ${location.pathname === item.to ? "bg-white text-black" : "text-gray-300 hover:bg-gray-900"}`}
            aria-current={location.pathname === item.to ? "page" : undefined}
            tabIndex={0}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </aside>
  );
}
