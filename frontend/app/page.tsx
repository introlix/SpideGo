import { SearchInput } from "@/components/search-input";


export default function Home() {

  return (
    <div className="flex flex-1 flex-col items-center justify-center space-y-7 bg-[#202020] font-sans">
      <h1 className="-mt-20 text-7xl font-bold text-white">SpideGo</h1>
      <div className="w-full max-w-2xl">
        <SearchInput q="" />
      </div>
    </div>
  );
}