import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router";
import { MovieCard } from "../components/movie-card";
import { TVInstructions } from "../components/tv-instructions";
import { TVSearchBox } from "../components/tv-search-box";
import { movies } from "../data/mock-data";
import { ArrowLeft } from "lucide-react";

export function MoviesScreen() {
  const navigate = useNavigate();
  const [focusedIndex, setFocusedIndex] = useState(-1); // Start at search box
  const [searchQuery, setSearchQuery] = useState("");
  const COLUMNS = 6;

  const filteredMovies = useMemo(() => {
    if (!searchQuery.trim()) return movies;
    return movies.filter((movie) =>
      movie.title.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [searchQuery]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // If in search box
      if (focusedIndex === -1) {
        switch (e.key) {
          case "ArrowDown":
            e.preventDefault();
            if (filteredMovies.length > 0) {
              setFocusedIndex(0);
            }
            break;
          case "Backspace":
          case "Escape":
            if (!searchQuery) {
              e.preventDefault();
              navigate("/");
            }
            break;
        }
      } else {
        // In grid
        switch (e.key) {
          case "ArrowLeft":
            e.preventDefault();
            setFocusedIndex((prev) => Math.max(0, prev - 1));
            break;
          case "ArrowRight":
            e.preventDefault();
            setFocusedIndex((prev) =>
              Math.min(filteredMovies.length - 1, prev + 1)
            );
            break;
          case "ArrowUp":
            e.preventDefault();
            const newUpIndex = focusedIndex - COLUMNS;
            if (newUpIndex < 0) {
              setFocusedIndex(-1); // Back to search
            } else {
              setFocusedIndex(newUpIndex);
            }
            break;
          case "ArrowDown":
            e.preventDefault();
            setFocusedIndex((prev) =>
              Math.min(filteredMovies.length - 1, prev + COLUMNS)
            );
            break;
          case "Backspace":
          case "Escape":
            e.preventDefault();
            navigate("/");
            break;
          case "Enter":
            e.preventDefault();
            console.log("Selected movie:", filteredMovies[focusedIndex]);
            break;
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [focusedIndex, searchQuery, filteredMovies, navigate]);

  return (
    <div className="min-h-screen bg-zinc-950 p-12">
      <TVInstructions />
      <div className="max-w-[1600px] mx-auto">
        <div className="flex items-center gap-6 mb-8">
          <button
            onClick={() => navigate("/")}
            className="text-zinc-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="w-8 h-8" />
          </button>
          <h1 className="text-5xl font-bold text-white">Movies</h1>
        </div>

        <div className="mb-8">
          <TVSearchBox
            value={searchQuery}
            onChange={setSearchQuery}
            focused={focusedIndex === -1}
            onFocus={() => setFocusedIndex(-1)}
            placeholder="Search movies..."
          />
        </div>

        {filteredMovies.length > 0 ? (
          <div className="grid grid-cols-6 gap-6">
            {filteredMovies.map((movie, index) => (
              <MovieCard
                key={movie.id}
                title={movie.title}
                year={movie.year}
                posterUrl={movie.posterUrl}
                focused={focusedIndex === index}
                onFocus={() => setFocusedIndex(index)}
                onClick={() =>
                  console.log("Clicked movie:", filteredMovies[focusedIndex])
                }
              />
            ))}
          </div>
        ) : (
          <div className="text-center text-zinc-500 text-2xl py-20">
            No movies found
          </div>
        )}
      </div>
    </div>
  );
}
