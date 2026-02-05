export interface Channel {
  id: number;
  name: string;
  number: number;
  logoUrl?: string;
}

export interface Movie {
  id: number;
  title: string;
  year: number;
  posterUrl?: string;
}

export interface Series {
  id: number;
  title: string;
  seasons: number;
  posterUrl?: string;
}

export const channels: Channel[] = [
  { id: 1, name: "HBO", number: 101 },
  { id: 2, name: "ESPN", number: 102 },
  { id: 3, name: "CNN", number: 103 },
  { id: 4, name: "Discovery", number: 104 },
  { id: 5, name: "National Geographic", number: 105 },
  { id: 6, name: "FOX", number: 106 },
  { id: 7, name: "NBC", number: 107 },
  { id: 8, name: "ABC", number: 108 },
  { id: 9, name: "CBS", number: 109 },
  { id: 10, name: "TNT", number: 110 },
  { id: 11, name: "AMC", number: 111 },
  { id: 12, name: "FX", number: 112 },
  { id: 13, name: "USA Network", number: 113 },
  { id: 14, name: "TBS", number: 114 },
  { id: 15, name: "Comedy Central", number: 115 },
  { id: 16, name: "MTV", number: 116 },
  { id: 17, name: "VH1", number: 117 },
  { id: 18, name: "History", number: 118 },
  { id: 19, name: "A&E", number: 119 },
  { id: 20, name: "Syfy", number: 120 },
];

export const movies: Movie[] = [
  { id: 1, title: "The Shawshank Redemption", year: 1994 },
  { id: 2, title: "The Godfather", year: 1972 },
  { id: 3, title: "The Dark Knight", year: 2008 },
  { id: 4, title: "Pulp Fiction", year: 1994 },
  { id: 5, title: "Forrest Gump", year: 1994 },
  { id: 6, title: "Inception", year: 2010 },
  { id: 7, title: "Fight Club", year: 1999 },
  { id: 8, title: "The Matrix", year: 1999 },
  { id: 9, title: "Goodfellas", year: 1990 },
  { id: 10, title: "Interstellar", year: 2014 },
  { id: 11, title: "The Silence of the Lambs", year: 1991 },
  { id: 12, title: "Saving Private Ryan", year: 1998 },
  { id: 13, title: "The Green Mile", year: 1999 },
  { id: 14, title: "Gladiator", year: 2000 },
  { id: 15, title: "The Departed", year: 2006 },
  { id: 16, title: "The Prestige", year: 2006 },
  { id: 17, title: "Memento", year: 2000 },
  { id: 18, title: "The Usual Suspects", year: 1995 },
  { id: 19, title: "American History X", year: 1998 },
  { id: 20, title: "The Lion King", year: 1994 },
];

export const series: Series[] = [
  { id: 1, title: "Breaking Bad", seasons: 5 },
  { id: 2, title: "Game of Thrones", seasons: 8 },
  { id: 3, title: "The Sopranos", seasons: 6 },
  { id: 4, title: "The Wire", seasons: 5 },
  { id: 5, title: "Stranger Things", seasons: 4 },
  { id: 6, title: "The Crown", seasons: 6 },
  { id: 7, title: "Better Call Saul", seasons: 6 },
  { id: 8, title: "The Office", seasons: 9 },
  { id: 9, title: "Friends", seasons: 10 },
  { id: 10, title: "Sherlock", seasons: 4 },
  { id: 11, title: "Westworld", seasons: 4 },
  { id: 12, title: "House of Cards", seasons: 6 },
  { id: 13, title: "Narcos", seasons: 3 },
  { id: 14, title: "Black Mirror", seasons: 6 },
  { id: 15, title: "Ozark", seasons: 4 },
  { id: 16, title: "The Mandalorian", seasons: 3 },
  { id: 17, title: "Succession", seasons: 4 },
  { id: 18, title: "Peaky Blinders", seasons: 6 },
  { id: 19, title: "The Witcher", seasons: 3 },
  { id: 20, title: "Squid Game", seasons: 2 },
];

export const otherChannels: Channel[] = [
  { id: 21, name: "BBC World News", number: 201 },
  { id: 22, name: "Cartoon Network", number: 202 },
  { id: 23, name: "Nickelodeon", number: 203 },
  { id: 24, name: "Disney Channel", number: 204 },
  { id: 25, name: "Food Network", number: 205 },
  { id: 26, name: "HGTV", number: 206 },
  { id: 27, name: "Travel Channel", number: 207 },
  { id: 28, name: "Animal Planet", number: 208 },
  { id: 29, name: "E! Entertainment", number: 209 },
  { id: 30, name: "Bravo", number: 210 },
  { id: 31, name: "Lifetime", number: 211 },
  { id: 32, name: "TLC", number: 212 },
  { id: 33, name: "Science Channel", number: 213 },
  { id: 34, name: "Weather Channel", number: 214 },
  { id: 35, name: "Golf Channel", number: 215 },
  { id: 36, name: "Tennis Channel", number: 216 },
  { id: 37, name: "MLB Network", number: 217 },
  { id: 38, name: "NFL Network", number: 218 },
  { id: 39, name: "NBA TV", number: 219 },
  { id: 40, name: "NHL Network", number: 220 },
];