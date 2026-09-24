import './LandingScreen.css';

export default function LandingScreen() {
  return (
    <div className="min-h-screen bg-[#06090E] text-slate-100 selection:bg-cyan-500/30 selection:text-cyan-200">
      {/* Background ambient radial glows */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[900px] h-[500px] bg-gradient-to-b from-cyan-500/15 via-emerald-500/10 to-transparent blur-3xl opacity-70" />
        <div className="absolute top-[35%] -left-40 w-[500px] h-[500px] bg-cyan-600/10 blur-[140px]" />
        <div className="absolute top-[65%] -right-40 w-[500px] h-[500px] bg-emerald-600/10 blur-[140px]" />
      </div>

      {/* Top Navbar */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-[#06090E]/80 border-b border-white/[0.08]">
        <nav className="mx-auto max-w-7xl px-6 h-20 flex justify-between items-center">
          <div className="flex items-center gap-8">
            <a href="/" className="text-xl font-black text-white flex items-center gap-3 tracking-tight group">
              <span className="size-10 rounded-xl bg-gradient-to-br from-cyan-400 to-emerald-500 text-[#06090E] grid place-items-center font-black text-lg shadow-[0_0_20px_rgba(6,182,212,0.4)] group-hover:scale-105 transition-transform">
                W
              </span>
              <span>Whetzy</span>
            </a>
            <div className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-400">
              <a href="#features" className="hover:text-cyan-400 transition-colors">Features</a>
              <a href="#how" className="hover:text-cyan-400 transition-colors">Methodology</a>
              <a href="#tracks" className="hover:text-cyan-400 transition-colors">Certifications</a>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <a href="/auth" className="text-sm font-semibold text-slate-300 hover:text-white transition-colors px-3 py-2">
              Sign in
            </a>
            <a
              href="/auth"
              className="relative group rounded-full p-[1px] overflow-hidden focus:outline-none"
            >
              <span className="absolute inset-0 bg-gradient-to-r from-cyan-500 to-emerald-500 rounded-full group-hover:opacity-100 transition-opacity" />
              <span className="relative block px-5 py-2.5 rounded-full bg-[#0D141F] text-sm font-bold text-white group-hover:bg-transparent transition-colors">
                Start learning free →
              </span>
            </a>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="relative z-10 pt-20 pb-28 px-6">
        <div className="mx-auto max-w-5xl text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/30 bg-cyan-950/40 px-4 py-1.5 text-xs font-semibold text-cyan-300 backdrop-blur-md mb-8 shadow-[0_0_15px_rgba(6,182,212,0.15)]">
            <span className="size-2 rounded-full bg-cyan-400 animate-pulse" />
            Adaptive Bilingual Intelligence 2.0
          </div>
          <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.1] text-white">
            Lessons that rewire themselves <br className="hidden md:inline" />
            <span className="bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 bg-clip-text text-transparent">
              around your exact knowledge gap.
            </span>
          </h1>
          <p className="mt-6 text-lg md:text-xl text-slate-400 max-w-2xl mx-auto leading-relaxed">
            Never waste time on what you already mastered. Whetzy blends real-time diagnostic evaluation, native English/Spanish tracks and instant AI reasoning to get you certified in record time.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="/auth"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-gradient-to-r from-cyan-500 to-emerald-500 text-[#06090E] font-black text-base shadow-[0_0_30px_rgba(6,182,212,0.35)] hover:shadow-[0_0_40px_rgba(16,185,129,0.5)] hover:-translate-y-0.5 transition-all"
            >
              Start Diagnostic Free
            </a>
            <a
              href="#how"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-[#0D141F] border border-white/10 text-slate-300 font-semibold hover:border-cyan-500/50 hover:text-white transition-all flex items-center justify-center gap-2"
            >
              See how the engine works
            </a>
          </div>

          <div className="mt-12 flex items-center justify-center gap-8 text-xs font-medium text-slate-500 uppercase tracking-widest">
            <span>✓ No credit card required</span>
            <span>•</span>
            <span>✓ Bilingual Spanish/English</span>
            <span>•</span>
            <span>✓ Verifiable Certificates</span>
          </div>
        </div>

        {/* Interactive preview showcase card */}
        <div className="mt-16 mx-auto max-w-4xl rounded-2xl border border-white/[0.12] bg-[#0D141F]/80 backdrop-blur-2xl p-6 md:p-8 shadow-2xl shadow-cyan-950/40 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-cyan-500/10 blur-[100px] pointer-events-none" />
          <div className="flex items-center justify-between border-b border-white/[0.08] pb-4 mb-6">
            <div className="flex items-center gap-3">
              <span className="size-3 rounded-full bg-red-500/80" />
              <span className="size-3 rounded-full bg-amber-500/80" />
              <span className="size-3 rounded-full bg-emerald-500/80" />
              <span className="text-xs font-mono text-slate-400 ml-2">diagnostic_adaptive_runner.ts</span>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded bg-emerald-950/60 text-emerald-400 border border-emerald-500/30">
              Live Session
            </span>
          </div>
          <div className="text-left space-y-4">
            <p className="text-xs font-bold text-cyan-400 tracking-wider uppercase">Adaptive Challenge #04 • SQL & System Architecture</p>
            <h3 className="text-lg md:text-xl font-bold text-white">
              Which indexing strategy maintains sub-10ms latency under high concurrent writes without locking the table?
            </h3>
            <div className="grid sm:grid-cols-2 gap-3 pt-2">
              <div className="p-4 rounded-xl border border-white/[0.08] bg-[#162030]/50 text-slate-300 text-sm hover:border-cyan-500/40 transition-colors cursor-pointer">
                A) Clustered index on auto-incrementing surrogate ID
              </div>
              <div className="p-4 rounded-xl border border-emerald-500/50 bg-emerald-950/20 text-emerald-300 text-sm font-semibold flex items-center justify-between">
                <span>B) Partial index with write-optimized BRIN</span>
                <span className="text-xs bg-emerald-500/20 px-2 py-0.5 rounded text-emerald-300">Optimal Match</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section id="features" className="relative z-10 py-24 px-6 border-t border-white/[0.06] bg-[#0A0F17]/50">
        <div className="mx-auto max-w-6xl">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">
              Built like a high-speed learning engine.
            </h2>
            <p className="mt-4 text-slate-400">
              Every detail is engineered to maximize retention and minimize wasted screen time.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            <div className="p-8 rounded-2xl border border-white/[0.08] bg-[#0D141F] hover:border-cyan-500/40 transition-all group">
              <div className="size-12 rounded-xl bg-cyan-950/60 border border-cyan-500/30 grid place-items-center text-cyan-400 text-xl font-bold group-hover:scale-110 transition-transform">
                ⚡
              </div>
              <h3 className="mt-6 text-xl font-bold text-white">Adaptive Difficulty</h3>
              <p className="mt-3 text-sm text-slate-400 leading-relaxed">
                The algorithm recalculates your knowledge frontier on every keystroke. Zero filler questions.
              </p>
            </div>

            <div className="p-8 rounded-2xl border border-white/[0.08] bg-[#0D141F] hover:border-emerald-500/40 transition-all group">
              <div className="size-12 rounded-xl bg-emerald-950/60 border border-emerald-500/30 grid place-items-center text-emerald-400 text-xl font-bold group-hover:scale-110 transition-transform">
                🌐
              </div>
              <h3 className="mt-6 text-xl font-bold text-white">Native Dual Language</h3>
              <p className="mt-3 text-sm text-slate-400 leading-relaxed">
                Switch seamlessly between Spanish and English mid-lesson without losing progress or context.
              </p>
            </div>

            <div className="p-8 rounded-2xl border border-white/[0.08] bg-[#0D141F] hover:border-purple-500/40 transition-all group">
              <div className="size-12 rounded-xl bg-purple-950/60 border border-purple-500/30 grid place-items-center text-purple-400 text-xl font-bold group-hover:scale-110 transition-transform">
                🤖
              </div>
              <h3 className="mt-6 text-xl font-bold text-white">24/7 AI Tutor Core</h3>
              <p className="mt-3 text-sm text-slate-400 leading-relaxed">
                Instant interactive breakdowns, edge-case hints and tailored code explanations when you get stuck.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 3-Step Methodology */}
      <section id="how" className="relative z-10 py-24 px-6 border-t border-white/[0.06]">
        <div className="mx-auto max-w-6xl">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">
              From zero to verified in three moves.
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="relative p-8 rounded-2xl border border-white/[0.08] bg-[#0D141F]">
              <span className="size-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 font-black text-base grid place-items-center">
                1
              </span>
              <h3 className="mt-6 text-lg font-bold text-white">Choose your track</h3>
              <p className="mt-2 text-sm text-slate-400">
                Select from backend, databases, frontend and devops. A quick placement check locks in your level.
              </p>
            </div>

            <div className="relative p-8 rounded-2xl border border-white/[0.08] bg-[#0D141F]">
              <span className="size-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-black text-base grid place-items-center">
                2
              </span>
              <h3 className="mt-6 text-lg font-bold text-white">Train dynamically</h3>
              <p className="mt-2 text-sm text-slate-400">
                Bite-sized diagnostic quizzes, live code runners and AI corrections adapt dynamically to you.
              </p>
            </div>

            <div className="relative p-8 rounded-2xl border border-white/[0.08] bg-[#0D141F]">
              <span className="size-10 rounded-xl bg-teal-500/10 border border-teal-500/30 text-teal-400 font-black text-base grid place-items-center">
                3
              </span>
              <h3 className="mt-6 text-lg font-bold text-white">Earn verification</h3>
              <p className="mt-2 text-sm text-slate-400">
                Pass the final mock exams and unlock tamper-proof certificates with granular skill breakdowns.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Bottom CTA Banner */}
      <section className="relative z-10 py-20 px-6">
        <div className="mx-auto max-w-5xl rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-cyan-950/60 via-[#0D141F] to-emerald-950/60 p-12 md:p-16 text-center shadow-[0_0_50px_rgba(6,182,212,0.15)] backdrop-blur-xl relative overflow-hidden">
          <div className="absolute -top-24 -left-24 size-64 bg-cyan-500/20 blur-3xl pointer-events-none" />
          <h2 className="text-3xl md:text-5xl font-extrabold text-white tracking-tight">
            Ready to upgrade how you learn?
          </h2>
          <p className="mt-4 text-slate-400 max-w-xl mx-auto">
            Join hundreds of developers leveling up with precision learning. Free to start, cancel anytime.
          </p>
          <div className="mt-8">
            <a
              href="/auth"
              className="inline-flex items-center gap-2 px-9 py-4 rounded-xl bg-gradient-to-r from-cyan-400 to-emerald-400 text-[#06090E] font-black text-base shadow-[0_0_30px_rgba(6,182,212,0.4)] hover:scale-105 transition-transform"
            >
              Get Started for Free →
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-white/[0.08] py-12 px-6 bg-[#04060A]">
        <div className="mx-auto max-w-7xl flex flex-col md:flex-row justify-between items-center gap-6 text-sm text-slate-500">
          <div className="flex items-center gap-3">
            <span className="size-6 rounded-lg bg-cyan-500/20 text-cyan-400 font-black text-xs grid place-items-center">
              W
            </span>
            <span className="font-bold text-slate-300">Whetzy Learning Inc.</span>
          </div>
          <div>© 2026 Whetzy. Precision bilingual learning engine.</div>
          <div className="flex items-center gap-6">
            <a href="/legal" className="hover:text-slate-300 transition-colors">Privacy & Terms</a>
            <a href="/auth" className="hover:text-slate-300 transition-colors">Login</a>
          </div>
        </div>
      </footer>
    </div>
  );
}
