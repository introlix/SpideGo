import { SearchInput } from "@/components/search-input";
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
    { name: "All", value: "all", link: `search?q=${params.q}&tab=all` },
    { name: "Image", value: "image", link: `search?q=${params.q}&tab=image` },
    { name: "Video", value: "video", link: `search?q=${params.q}&tab=video` },
    { name: "News", value: "news", link: `search?q=${params.q}&tab=news` },
    { name: "Map", value: "map", link: `search?q=${params.q}&tab=map` },
    { name: "Forums", value: "forums", link: `search?q=${params.q}&tab=forums` },
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

        <Tabs value={params.tab || "all"} className={"sm:ml-44 mx-10 mt-3"}>
          <TabsList variant="line">
            {tabs.map((data, index) => (
              <Link key={index} href={data.link}><TabsTrigger value={data.value}>{data.name}</TabsTrigger></Link>
            ))}
          </TabsList>
        </Tabs>
      </div>

      <main className="mx-auto max-w-7xl px-6 pt-8">
        {/* Search results will go here */}
      </main>
    </div>
  );
}