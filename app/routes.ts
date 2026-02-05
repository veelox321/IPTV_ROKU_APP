import { createBrowserRouter } from "react-router";
import { HomeScreen } from "./screens/home-screen";
import { LiveScreen } from "./screens/live-screen";
import { MoviesScreen } from "./screens/movies-screen";
import { SeriesScreen } from "./screens/series-screen";
import { OthersScreen } from "./screens/others-screen";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: HomeScreen,
  },
  {
    path: "/live",
    Component: LiveScreen,
  },
  {
    path: "/movies",
    Component: MoviesScreen,
  },
  {
    path: "/series",
    Component: SeriesScreen,
  },
  {
    path: "/others",
    Component: OthersScreen,
  },
]);