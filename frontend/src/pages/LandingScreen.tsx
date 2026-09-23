export default function LandingScreen() {
  return (
    <div className="min-h-screen bg-white">
      <header className="absolute inset-x-0 top-0 z-20">
        <nav className="mx-auto max-w-6xl px-5 py-5 flex justify-between items-center">
          <span className="text-lg font-black text-white flex items-center gap-2">
            <span className="size-8 rounded-xl bg-white/15 grid place-items-center">W</span>Whetzy
          </span>
          <div className="flex items-center gap-3">
            <a href="/auth" className="text-sm font-semibold text-white/90 hover:text-white">Sign in</a>
            <a href="/auth" className="rounded-full bg-white px-5 py-2 text-sm font-bold text-indigo-600">Start free</a>
          </div>
        </nav>
      </header>

      <section className="relative bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-700 px-5 pt-32 pb-20">
        <div className="mx-auto max-w-6xl grid lg:grid-cols-2 gap-12">
          <div className="text-white">
            <h1 className="text-5xl lg:text-6xl font-black leading-tight">Lessons that rewrite themselves around you.</h1>
            <p className="mt-5 text-lg text-white/80 max-w-xl">Whetzy blends an adaptive engine, bilingual lessons and an AI tutor so every session lands exactly at the edge of what you know.</p>
            <div className="mt-8 flex gap-3">
              <a href="/auth" className="rounded-full bg-white px-7 py-3.5 font-bold text-indigo-600 hover:-translate-y-0.5 transition">Start free</a>
              <a href="#how" className="rounded-full border-2 border-white/30 px-7 py-3.5 font-semibold text-white hover:bg-white/10 transition flex items-center gap-2">▶ See how</a>
            </div>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-24">
        <h2 className="text-4xl font-black">Three things that make Whetzy <span className="text-indigo-600">stick</span>.</h2>
        <div className="mt-10 grid md:grid-cols-3 gap-5">
          <div className="rounded-3xl border border-gray-200 bg-white p-6 hover:-translate-y-1 transition">
            <div className="size-11 rounded-2xl bg-indigo-100 text-indigo-600 grid place-items-center font-bold text-xl">⚡</div>
            <h3 className="mt-5 font-bold">Adaptive learning</h3>
            <p className="mt-2 text-sm text-gray-600">Engine re-scores every answer and rebuilds lessons around gaps.</p>
          </div>
          <div className="rounded-3xl border border-gray-200 bg-white p-6 hover:-translate-y-1 transition">
            <div className="size-11 rounded-2xl bg-indigo-100 text-indigo-600 grid place-items-center font-bold text-xl">🌐</div>
            <h3 className="mt-5 font-bold">Truly bilingual</h3>
            <p className="mt-2 text-sm text-gray-600">Learn in two languages at once. Switch mid-lesson, keep your streak.</p>
          </div>
          <div className="rounded-3xl border border-gray-200 bg-white p-6 hover:-translate-y-1 transition">
            <div className="size-11 rounded-2xl bg-indigo-100 text-indigo-600 grid place-items-center font-bold text-xl">🤖</div>
            <h3 className="mt-5 font-bold">AI tutor, 24/7</h3>
            <p className="mt-2 text-sm text-gray-600">Get hints, rewrites, or full explanations that know your history.</p>
          </div>
        </div>
      </section>

      <section id="how" className="bg-gray-50 px-5 py-24">
        <div className="mx-auto max-w-6xl">
          <h2 className="text-4xl font-black">From zero to certified in three moves.</h2>
          <ol className="mt-10 grid md:grid-cols-3 gap-5">
            <li className="rounded-3xl bg-white p-6"><div className="flex items-center gap-3"><span className="size-10 rounded-full bg-indigo-600 text-white font-black grid place-items-center">1</span></div><h3 className="mt-5 font-bold">Choose a skill</h3><p className="mt-2 text-sm text-gray-600">Pick from available tracks. A placement check sets your level.</p></li>
            <li className="rounded-3xl bg-white p-6"><div className="flex items-center gap-3"><span className="size-10 rounded-full bg-indigo-600 text-white font-black grid place-items-center">2</span></div><h3 className="mt-5 font-bold">Learn adaptive</h3><p className="mt-2 text-sm text-gray-600">Short sessions shift difficulty as you go. Nothing too easy or too hard.</p></li>
            <li className="rounded-3xl bg-white p-6"><div className="flex items-center gap-3"><span className="size-10 rounded-full bg-indigo-600 text-white font-black grid place-items-center">3</span></div><h3 className="mt-5 font-bold">Get certified</h3><p className="mt-2 text-sm text-gray-600">Earn certificates with skill breakdown ready to share.</p></li>
          </ol>
        </div>
      </section>

      <section className="px-5 pb-20">
        <div className="mx-auto max-w-6xl rounded-3xl bg-gradient-to-br from-indigo-600 to-purple-600 text-white px-6 py-16 text-center shadow-xl">
          <h2 className="text-5xl font-black">Your first lesson starts now.</h2>
          <p className="mt-4 opacity-80">No card required. Start free.</p>
          <a href="/auth" className="mt-8 inline-flex rounded-full bg-white px-8 py-4 font-bold text-indigo-600 hover:-translate-y-0.5 transition">Start learning</a>
        </div>
      </section>

      <footer className="border-t border-gray-200 px-5 py-10">
        <div className="mx-auto max-w-6xl flex justify-between items-center text-sm text-gray-600">
          <span className="font-bold text-gray-900">Whetzy</span>
          <span>© 2026 Whetzy. Learn in two languages.</span>
        </div>
      </footer>
    </div>
  );
}
