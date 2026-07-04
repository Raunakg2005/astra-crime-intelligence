import { createContext, useContext, useEffect, useState, ReactNode } from "react";

type Theme = "dark" | "light";
const ThemeCtx = createContext<{ theme: Theme; toggle: () => void }>({ theme: "dark", toggle: () => {} });

function applyTheme(t: Theme) {
  document.documentElement.classList.toggle("light", t === "light");
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem("astra-theme");
    return saved === "light" || saved === "dark" ? saved : "dark";
  });

  useEffect(() => {
    applyTheme(theme);
    localStorage.setItem("astra-theme", theme);
  }, [theme]);

  return (
    <ThemeCtx.Provider value={{ theme, toggle: () => setTheme((t) => (t === "dark" ? "light" : "dark")) }}>
      {children}
    </ThemeCtx.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export const useTheme = () => useContext(ThemeCtx);
