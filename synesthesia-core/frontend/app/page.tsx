"use client";

import { useState } from 'react';
import Visualizer from '../components/Visualizer';
import Knobs from '../components/Knobs';
import SearchBar from '../components/SearchBar';

export default function Home() {
  const [currentSong, setCurrentSong] = useState<any>(null);
  const [targetVector, setTargetVector] = useState<number[] | undefined>(undefined);

  const handleSearchSuccess = (data: any) => {
    console.log("Search Result:", data);
    setCurrentSong(data.metadata);
    setTargetVector(data.vector);
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-8 bg-black">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex mb-8">
        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">
          Synesthesia &nbsp;
          <code className="font-mono font-bold">v0.1.0</code>
        </p>
        <div className="fixed bottom-0 left-0 flex h-48 w-full items-end justify-center bg-gradient-to-t from-white via-white dark:from-black dark:via-black lg:static lg:h-auto lg:w-auto lg:bg-none">
          {currentSong ? (
            <div className="flex flex-col items-end text-right text-white">
              <span className="text-xs text-gray-400">NOW PLAYING</span>
              <span className="font-bold text-lg">{currentSong.title}</span>
              <span className="text-sm text-gray-300">{currentSong.artist}</span>
            </div>
          ) : (
            <span className="text-gray-500">No track selected</span>
          )}
        </div>
      </div>

      <div className="w-full max-w-5xl flex flex-col gap-8 relative">
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-50 w-full max-w-md">
          <SearchBar onSearchSuccess={handleSearchSuccess} />
        </div>
        <Visualizer targetVector={targetVector} />
        <Knobs />
      </div>
    </main>
  );
}
