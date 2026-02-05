import React from "react";
import { createBrowserRouter } from "react-router";
import { SessionShell } from "./components/session-shell";
import { HomeScreen } from "./screens/home-screen";
import { LiveScreen } from "./screens/live-screen";
import { MoviesScreen } from "./screens/movies-screen";
import { SeriesScreen } from "./screens/series-screen";
import { OthersScreen } from "./screens/others-screen";

export const router = createBrowserRouter([
  {
    path: "/",
    element: React.createElement(SessionShell, {
      Screen: HomeScreen,
    }),
  },
  {
    path: "/live",
    element: React.createElement(SessionShell, {
      Screen: LiveScreen,
    }),
  },
  {
    path: "/movies",
    element: React.createElement(SessionShell, {
      Screen: MoviesScreen,
    }),
  },
  {
    path: "/series",
    element: React.createElement(SessionShell, {
      Screen: SeriesScreen,
    }),
  },
  {
    path: "/others",
    element: React.createElement(SessionShell, {
      Screen: OthersScreen,
    }),
  },
]);
