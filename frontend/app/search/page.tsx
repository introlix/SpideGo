import { SearchInput } from "@/components/search-input";
import { SearchResults } from "@/components/search-results";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Link from "next/link";

export default async function SearchPage({
  searchParams,
}: {
  searchParams: Promise<{
    q?: string;
    tab?: string;
  }>;
}) {
  const params = await searchParams;

  const tabs = [
    { name: "All", value: "general", link: `search?q=${params.q}&tab=general` },
    { name: "Images", value: "images", link: `search?q=${params.q}&tab=images` },
    { name: "Video", value: "videos", link: `search?q=${params.q}&tab=videos` },
    { name: "News", value: "news", link: `search?q=${params.q}&tab=news` },
    { name: "Map", value: "map", link: `search?q=${params.q}&tab=map` },
    { name: "Forums", value: "it", link: `search?q=${params.q}&tab=it` },
    { name: "Music", value: "music", link: `search?q=${params.q}&tab=music` },
  ]

  return (
    <div className="min-h-screen bg-[#202020] text-white">
      <div className="fixed inset-x-0 top-0 z-40 border-b border-white/5 bg-[#202020]/90 backdrop-blur-xl">
        <div className="sm:flex items-center space-x-10 ml-10 mx-10 mt-5">
          <Link href={'/'}>
            <h1 className="text-center text-2xl font-bold text-white">SpideGo</h1>
          </Link>
          <div className="relative z-50 w-full max-w-2xl">
            <SearchInput q={params.q} />
          </div>
        </div>

        <Tabs value={params.tab || "all"} className={"sm:ml-44 sm:items-start items-center mt-3"}>
          <TabsList variant="line">
            {tabs.map((data, index) => (
              <Link key={index} href={data.link}><TabsTrigger value={data.value}>{data.name}</TabsTrigger></Link>
            ))}
          </TabsList>
        </Tabs>
      </div>

      <main className="px-6 pt-40">
        {params.q && <SearchResults query={params.q} tab={params.tab ?? "general"} />}
      </main>
    </div>
  );
}