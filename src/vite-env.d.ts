/// <reference types="vite/client" />

// React type declarations
declare module "react" {
  export function useState(initialState?: any): any;
  export function useEffect(effect: any, deps?: any): void;
  export function useCallback(callback: any, deps?: any): any;
  export function useRef(initialValue?: any): any;
  export function useMemo(factory: any, deps?: any): any;
  export function useContext(context: any): any;
  export function createContext(defaultValue?: any): any;
  export function forwardRef(render: any): any;
  export function memo(component: any): any;
  export namespace React {
    export interface FC<P = {}> {
      (props: P): any;
    }
    export interface ReactNode {}
    export interface CSSProperties {}
  }
  export = React;
  export as namespace React;
}

// React Router DOM type declarations
declare module "react-router-dom" {
  export function useParams(): any;
  export function useNavigate(): any;
  export function useLocation(): any;
  export function Link(props: any): any;
  export function NavLink(props: any): any;
  export function Outlet(props?: any): any;
  export function Navigate(props: any): any;
  export function BrowserRouter(props: any): any;
  export function Routes(props: any): any;
  export function Route(props: any): any;
}

declare module "*.svg" {
  const content: string;
  export default content;
}

declare module "*.png" {
  const content: string;
  export default content;
}

declare module "*.jpg" {
  const content: string;
  export default content;
}

declare module "*.jpeg" {
  const content: string;
  export default content;
}

declare module "*.gif" {
  const content: string;
  export default content;
}

declare module "*.webp" {
  const content: string;
  export default content;
}
