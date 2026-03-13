The JTC 2.0 次世代仕様定義書 (Remastered Edition)バージョン: 2.0.6最終更新日: 2026-03-08ドキュメント分類: システムアーキテクチャ・要求仕様書 (PRD)1. はじめに (Introduction)1.1 プロジェクトの背景と目的「The JTC 2.0」は、日本の伝統的大企業（JTC）における新規事業創出プロセスを、LLM（大規模言語モデル）とマルチエージェントシステムによって抜本的に効率化・高度化するためのシミュレーションプラットフォームである。初期バージョンにおいては、社内政治（激詰め会議）のシミュレーションとv0.devを用いたMVPの自動生成を実現したが、AI特有の「文脈の飛躍（ハルシネーション）」や「特定AIツールへのロックイン」といった課題が浮き彫りとなった。本刷新（Remastered）では、田所雅之氏の『起業の科学』で提唱される「カスタマープロブレムフィット（CPF）」から「プロブレムソリューションフィット（PSF）」に至る検証プロセスを、一切の論理的飛躍なくシステム上にマッピングする。LLMに対してPydanticを用いた厳格な「型（Schema）」を強制し、思考プロセスを細分化（Chain of Thought）することでハルシネーションを完全に排除する。1.2 最終成果物（システムのアウトプット）の再定義本システムは、特定のUI生成API（v0.dev等）を直接実行するアプローチを廃止する。代わって、システムの最終出力を**「Cursor、Windsurf、Google Antigravityなど、あらゆる自律型AIコーディングエージェントにそのまま入力可能な『完璧なプロンプト仕様書（AgentPromptSpec.md）』および『MVP実験計画書』の生成」**と再定義する。これにより、システムは陳腐化しない普遍的な「究極の要件定義エンジン」として機能する。2. コア・アーキテクチャと設計思想2.1 Pydantic駆動とChain of Thoughtによるハルシネーションの排除 (Schema-Driven Generation)AIの推論プロセスにおける文脈の喪失を防ぐため、すべてのLangGraphノードの出力は pydantic.BaseModel および extra="forbid" によって厳格に構造化される。これは、AIのプロンプトエンジニアリングにおける「Chain of Thought（思考の連鎖）」をシステムレベルで強制・可視化するアプローチである。 AIは「エンパシーマップ」からいきなり「機能（解決策）」を導き出すような論理の飛躍は絶対に許されない。必ず「代替品分析」→「バリュープロポジション」→「メンタルモデルダイアグラム」→「カスタマージャーニー」→「サイトマップとユーザーストーリー」という段階的なスキーマ（キャンバス）を一つずつ順番に埋めさせる。前のステップで出力されたキャンバスを次のステップの入力として連鎖させることで、段階的にプロダクトの解像度を上げていく。この緻密なフローにより、AI特有の「一般論に基づくもっともらしい嘘（ハルシネーション）」が入り込む余地を完全に排除する仕様としている。2.2 マルチエージェント・オーケストレーション (LangGraph)LangGraphを用いて、以下の3つの主要なサブグラフ（会議体）をオーケストレーションする。The JTC Board (社内承認シミュレーション): 財務部長、営業本部長、CPOによるビジネスモデルと実現可能性の激詰め。Virtual Market (仮想市場テスト): 仮想顧客エージェントによるソリューションに対する辛口レビューとコミットメント判定。The 3H Review (プロダクト磨き込み): Hacker（技術）、Hipster（UX）、Hustler（ビジネス）によるワイヤーフレームの多角的な検証。2.3 脱同一化UI (Pyxel) と「承認」演出システムのバックエンドで高度なビジネスロジックが進行する一方、ユーザーが直面するフロントエンドUIは「Pyxel」を用いた16色のレトロRPG風画面を維持する。これは、AIからの苛烈な批判やアイデアの否定を「ゲームのイベント」として脱同一化し、ユーザーの心理的安全性を担保するための極めて重要なアーキテクチャ的決定である。さらに、本システムでは各種キャンバス（代替品分析、カスタマージャーニー等）の生成プロセスが完了し、システムの検証を通るたびに、Pyxel画面上にドット絵の「承認」スタンプ（赤いハンコ）がダイナミックに押される演出が組み込まれる。JTCならではのハンコ文化を逆手にとり、ユーザーに「関門を突破した」という強烈な達成感と進行感を与える設計となっている。3. 全体ワークフロー (The Fitness Journey Workflow)本システムは、以下の6つのフェーズ、計14の主要ノード（ステップ）を順番に実行する。各キャンバスの生成後には「Human In the Loop (HITL) FBゲート」が挟まれ、ユーザーからの軌道修正を受け付ける。Phase 1: Idea Verification (アイデア検証)Step 1: Ideation & PEST Analysis (ideator_node)Tavily Search APIを用いてマクロ環境（PEST）の変曲点を検索。Good Crazyなビジネスアイデアを10個生成（LeanCanvas モデル）。[HITL Gate 1]: ユーザーが取り組むべき「Plan A」を選択。Phase 2: Customer / Problem Fit (顧客と課題の適合)Step 2: Persona & Empathy Mapping (persona_node)選択されたアイデアから、解像度の高い Persona と EmpathyMap を生成。Step 3: Alternative Analysis (alternative_analysis_node)現状の代替手段（Excel、既存SaaS等）を特定し、乗り換えの手間（スイッチングコスト）を上回る「10x Value（10倍の価値）」を推論する。Step 4: Value Proposition Design (vpc_node)顧客の「片付けるべき用事（Customer Jobs）」と「Pain/Gain」に対し、ソリューションが提供する「Pain Relievers（鎮痛剤）」と「Gain Creators（恩恵の創出）」がどう合致（Fit）しているかを検証・構造化する。[HITL Gate 1.5 - CPF Feedback]: Step 2〜4で生成されたモデルがPDF出力され、Pyxel上で「承認」スタンプが押される。ユーザーはPDFを確認し、必要に応じてペルソナやVPCの調整指示（FB）を入力できる。Step 5: Problem Interview RAG (transcript_ingestion_node)ユーザーが実施した顧客インタビューの音声文字起こし（PLAUD等）をLlamaIndexでベクトル化。CPOエージェントが「The Mom Test」の基準でファクトチェックを行う。Phase 3: Problem / Solution Fit (課題と解決策の適合)Step 6: Mental Model & Journey Mapping (mental_model_journey_node)ユーザーの行動の背後にある「思考の塔（信念・価値観）」を MentalModelDiagram として可視化。そのメンタルモデルに基づく時系列の行動を CustomerJourney にマッピングし、最もPainの強いタッチポイントから UserStory を抽出する。Step 7: Sitemap & Lo-Fi Wireframing (sitemap_wireframe_node)アプリ全体のURL構造とページ遷移の全体像を Sitemap として定義する。定義したサイトマップに基づき、ユーザーストーリーを達成するための特定画面の構造を、デザイン要素を排除した純粋なテキスト階層 WireframeText モデルとして出力する。[HITL Gate 1.8 - PSF Feedback]: メンタルモデル、ジャーニー、サイトマップがPDF出力され、Pyxel上で「承認」スタンプが押される。ユーザーはPDFを確認し、機能の削ぎ落としやストーリーの修正指示（FB）を与える。Phase 4: Validation & Review (仮説の検証と磨き込み)Step 8: Virtual Solution Interview (virtual_customer_node)ペルソナとメンタルモデルのプロンプトを注入された「仮想顧客エージェント」に対してワイヤーフレームとサイトマップを提示。仮想顧客は「これならいくら払うか？」「どこで離脱するか？」をフィードバックする。[HITL Gate 2]: ユーザーは仮想顧客の反応を見て、アイデアをピボットするか進行するかを決定。Step 9: JTC Board Simulation (jtc_simulation_node)財務部長（ROI・コスト）、営業本部長（カニバリ・売りやすさ）による激詰め。Pyxel UIで描画。Step 10: 3H Review (3h_review_node)Hacker（技術的実現性）、Hipster（UXの摩擦）、Hustler（ユニットエコノミクス）によるプロダクト仕様の最終レビューと修正。Phase 5 & 6: Output Generation (最終成果物の生成)Step 11: Agent Prompt Spec Generation (spec_generation_node)これまでの全コンテキストを集約し、AIコーディングツール向けの完全なマークダウンプロンプト AgentPromptSpec を生成。Step 12: Experiment Planning (experiment_planning_node)生成されたMVPを用いて「何を・どう測るか」を定義する ExperimentPlan（AARRRベースのKPIツリー）を生成。[HITL Gate 3 - Final Output FB]: 実験計画と最終仕様の生成完了時、最後の「承認」スタンプが押され、一連の最終成果物がPDF化される。Step 13: Governance Check (governance_node)JTCの稟議書（Ringi-Sho）フォーマットで最終レポートを出力。4. 追加・変更されるドメインモデル詳細 (Pydantic Schemas)AIのハルシネーションを防ぎ、文脈を維持するための新規データモデル定義。4.1 バリュープロポジションキャンバス (ValuePropositionCanvas)class CustomerProfile(BaseModel):
    customer_jobs: list[str] = Field(..., description="顧客が片付けたい用事・社会的/感情的タスク")
    pains: list[str] = Field(..., description="ジョブの実行を妨げるリスクやネガティブな感情")
    gains: list[str] = Field(..., description="ジョブの実行によって得たい恩恵や期待")

class ValueMap(BaseModel):
    products_and_services: list[str] = Field(..., description="提供する主要な製品・サービスのリスト")
    pain_relievers: list[str] = Field(..., description="顧客のPainを具体的にどう取り除くか")
    gain_creators: list[str] = Field(..., description="顧客のGainを具体的にどう創出するか")

class ValuePropositionCanvas(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_profile: CustomerProfile
    value_map: ValueMap
    fit_evaluation: str = Field(..., description="Pain RelieversとPain、Gain CreatorsとGainが論理的にFitしているかの検証結果")
4.2 メンタルモデルダイアグラム (MentalModelDiagram)class MentalTower(BaseModel):
    belief: str = Field(..., description="ユーザーの根底にある信念や価値観（例：『時間を無駄にしたくない』）")
    cognitive_tasks: list[str] = Field(..., description="その信念に基づいて頭の中で行っているタスクや判断")

class MentalModelDiagram(BaseModel):
    model_config = ConfigDict(extra="forbid")
    towers: list[MentalTower] = Field(..., description="ユーザーの思考空間を構成する複数の思考の塔")
    feature_alignment: str = Field(..., description="定義した思考の塔（タワー）に対して、提供する機能がどう寄り添い、サポートしているかのマッピング")
4.3 代替品分析モデル (AlternativeAnalysis)class AlternativeTool(BaseModel):
    name: str = Field(..., description="代替品の名前（例：Excel、手作業、既存SaaS）")
    financial_cost: str = Field(..., description="金銭的コスト")
    time_cost: str = Field(..., description="時間的コスト")
    ux_friction: str = Field(..., description="ユーザーが感じる最大のストレス・摩擦")

class AlternativeAnalysis(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_alternatives: list[AlternativeTool]
    switching_cost: str = Field(..., description="ユーザーが乗り換える際に発生するコストや手間")
    ten_x_value: str = Field(..., description="スイッチングコストを圧倒する、代替品の10倍の価値（UVP）")
4.4 カスタマージャーニーモデル (CustomerJourney)class JourneyPhase(BaseModel):
    phase_name: str = Field(..., description="フェーズ名（例：認知、検討、利用中、離脱）")
    touchpoint: str = Field(..., description="顧客とシステム/環境の接点")
    customer_action: str = Field(..., description="顧客の具体的な行動")
    mental_tower_ref: str = Field(..., description="この行動を裏付けているMentalTowerの信念")
    pain_points: list[str] = Field(..., description="このフェーズで感じる痛みや不満")
    emotion_score: int = Field(..., ge=-5, le=5, description="感情の起伏（-5から5）")

class CustomerJourney(BaseModel):
    model_config = ConfigDict(extra="forbid")
    phases: list[JourneyPhase] = Field(..., min_length=3, max_length=7)
    worst_pain_phase: str = Field(..., description="最もPainが深い（解決すべき）フェーズの名前")
4.5 サイトマップ＆ユーザーストーリーモデル (SitemapAndStory)class Route(BaseModel):
    path: str = Field(..., description="URLパス (例: /, /dashboard, /login)")
    name: str = Field(..., description="ページ名")
    purpose: str = Field(..., description="このページの目的")
    is_protected: bool = Field(..., description="認証が必要なページかどうか")

class UserStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    as_a: str = Field(..., description="誰として（Persona）")
    i_want_to: str = Field(..., description="何をしたいか（Action）")
    so_that: str = Field(..., description="なぜなら〜を達成したいから（Goal/Value）")
    acceptance_criteria: list[str] = Field(..., description="このストーリーが満たされたとする受け入れ条件")
    target_route: str = Field(..., description="このアクションを主に行うURLパス")

class SitemapAndStory(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sitemap: list[Route] = Field(..., description="アプリケーション全体のURL・ルーティング構成")
    core_story: UserStory = Field(..., description="MVPとして検証すべき最重要な単一のストーリー")
4.6 実験計画モデル (ExperimentPlan)class MetricTarget(BaseModel):
    metric_name: str = Field(..., description="指標名（例：Day7 Retention）")
    target_value: str = Field(..., description="PMF達成とみなす目標値（例：40%以上）")
    measurement_method: str = Field(..., description="計測方法")

class ExperimentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    riskiest_assumption: str = Field(..., description="今回検証する最もリスクの高い前提条件")
    experiment_type: str = Field(..., description="MVPの型（例：LP、コンシェルジュ、Wizard of Oz）")
    acquisition_channel: str = Field(..., description="初期の100人をどこから連れてくるか")
    aarrr_metrics: list[MetricTarget] = Field(..., description="AARRRフレームワークに基づく追跡指標")
    pivot_condition: str = Field(..., description="どのような結果になれば即撤退（ピボット）すべきか")
4.7 AIエージェント向け仕様書モデル (AgentPromptSpec)class StateMachine(BaseModel):
    success: str = Field(..., description="データ正常時の完全なレイアウト")
    loading: str = Field(..., description="Skeletonコンポーネントを用いた待機UI")
    error: str = Field(..., description="フォールバックUIとRetryボタンの配置")
    empty: str = Field(..., description="データ0件時のCTAを含むEmpty State")

class AgentPromptSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sitemap: str = Field(..., description="アプリ全体のルーティングと情報アーキテクチャ")
    routing_and_constraints: str = Field(..., description="SSR/Client Componentの境界、UIライブラリの指定")
    core_user_story: UserStory
    state_machine: StateMachine
    validation_rules: str = Field(..., description="Zodスキーマやエッジケースの要件")
    mermaid_flowchart: str = Field(..., description="Mermaid構文による状態遷移・データフロー図")
5. エージェント定義 (Agents Definition)LangGraphノードを駆動する専用AIエージェントのプロンプト方針。【重要原則：コンテキストの絶対的継承】本システムにおけるすべてのエージェントは、自己の学習データや直感のみに頼って（ゼロベースで）アイデアや機能を提案してはならない。Phase 1〜3のChain of Thoughtプロセスで段階的に生成されたすべての構造化データ（ペルソナ、エンパシーマップ、VPC、メンタルモデルダイアグラム、カスタマージャーニー、サイトマップ等）を「絶対的な前提条件」としてプロンプトに読み込む。エージェント群は、これら「顧客理解のキャンバス群」を前提としてのみ、効果的なプロダクトの検証と仕様構築を行うよう厳格に制御される。5.1 仮想顧客エージェント (Virtual Customer)Role: 対象となるペルソナそのもの。Prompt System: "あなたは [Persona Name] です。あなたの思考の根底には [MentalModelDiagram.towers] のような信念があり、現在は [AlternativeTool] を使っていますが、[Pain] に深く悩んでいます。今から提案される機能について、絶対に忖度せず、自分がお金を払ってでも使いたいか、それとも不要かを厳しくフィードバックしてください。特に『面倒くささ（スイッチングコスト）』には敏感に反応してください。"5.2 The 3H Review AgentsHacker Agent: "【前提とするサイトマップと機能要件を遵守しつつ】技術的負債、スケーラビリティ、セキュリティの観点からワイヤーフレームをレビューせよ。不要に複雑なDB構造やリアルタイム通信を避け、スプレッドシートや既存APIのモックで代替できないか追求せよ。"Hipster Agent: "【前提とするメンタルモデルとペルソナを遵守しつつ】ユーザーの『Don't make me think（考えさせるな）』の原則に基づきUXをレビューせよ。メンタルモデルに反するオンボーディングの摩擦、タップ回数の多さ、エラー時の不親切さを指摘せよ。"Hustler Agent: "【前提とする代替品分析とVPCを遵守しつつ】ユニットエコノミクス（LTV > 3x CAC）の観点からビジネスモデルをレビューせよ。誰がどうやって見つけるのか、なぜ継続してお金を払うのかを厳しく問いただせ。"5.3 Builder Agent (役割変更)Old Role: v0.devのAPIを叩いてURLを生成する。New Role: これまで生成されたすべてのコンテキスト（VPC、メンタルモデル、ジャーニー、ストーリー、サイトマップ、3Hのレビュー結果）を統合前提として読み込む。「引き算の思考（ユーザーのPain解決に直結しない不要な機能の削除）」を適用した上で、あらゆるAIコーディングツールに通用する究極の要件定義書 AgentPromptSpec を生成する。6. 最終成果物フォーマット (Output Specifications)システムが正常に完走した場合、ローカルディレクトリに以下のファイルが出力される。6.1 MVP_PROMPT_SPEC.mdCursor、Windsurf、v0.dev、Google AntigravityなどのAIエディタ/エージェントのチャット欄にそのままコピー＆ペーストするためのファイル。# 🤖 System & Context
- Role: Expert Frontend Engineer & UI/UX Designer
- Stack: Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, Lucide-react
- Principles: One Feature One Value, Mobile First, Accessible (WCAG 2.1)
- Routing & Components: [SSR/Clientの境界、UIライブラリの厳格な制約]

# 🗺️ Sitemap & Information Architecture
- `/` : ランディングページ（未認証） - 価値提案と登録導線
- `/login` : 認証ページ
- `/dashboard` : メイン機能（Core User Storyの実行場所）
※ AIへの指示: 上記で定義された以外の不要なページ（/settings, /profile等）へのリンクは生成せず、遷移できないようにすること。

# 🎯 Core User Story
- As a: [Persona]
- I want to: [Action]
- So that: [Value/Goal]
- Target Route: [該当するURL, 例: /dashboard]
- Acceptance Criteria:
  - [受け入れ条件1]
  - [受け入れ条件2]

# 📊 Data Schema & Flow
- TypeScript Interfaces:
  ```typescript
  // AIが生成しやすいよう、厳格な型定義とモックJSONの構造を定義
Validation Rules: [Zodを用いたバリデーション要件（例: 8文字以上、記号必須など）]🔄 State Machine (Mermaid)stateDiagram-v2
    [*] --> Idle
    Idle --> Loading : Submit form
    Loading --> Success : API 200 OK
    Loading --> Error : API 4xx/5xx
    Error --> Idle : Click Retry
🖥️ UI Structure & StatesSuccess State: [データ正常時のコンポーネント配置・レイアウト]Loading State: [スピナーではなく、shadcn/uiのSkeleton配置指示]Empty State: [データがない時のイラストとCTAボタン配置]Error State: [フォールバックUIと再試行ボタン]🖱️ Interaction & A11yInteractions: [ボタンクリック時のトースト通知等]Accessibility: [ARIAラベル、キーボード操作要件]
### 6.2 `EXPERIMENT_PLAN.md`

生成したMVPを使って、現実世界でどのように仮説検証を行うかを示したスプリント計画書。
ランディングページへの流入経路、コンシェルジュ対応のマニュアル方針、そして「PMF達成」を判定するためのAARRR指標のボーダーラインが記載される。

### 6.3 キャンバス・ドキュメントのPDF出力とPyxel承認演出 【新規】

システムは各推論フェーズの節目で以下の処理を実行し、人間との共創（HITL）を円滑に行う。

1. **対象ドキュメント:**
   * バリュープロポジションキャンバス
   * メンタルモデルダイアグラム
   * 代替品分析モデル
   * カスタマージャーニーモデル
   * サイトマップ＆ユーザーストーリーモデル
   * 実験計画モデル
2. **Pyxel上での承認演出:** 各ドキュメントがPydanticモデルとして正常に生成された直後、PyxelのレトロUI画面上に赤い「承認」ハンコがドーンと押されるSEとアニメーションが再生される。
3. **高解像度PDFの簡易出力:** 同時に、裏側で各種キャンバスが視覚的に整理された高解像度PDFファイルとしてローカル（`/outputs/canvas/` ディレクトリ等）に出力される。
4. **Human In the Loop (HITL) のフィードバック:** ユーザーは出力されたPDFを簡易にレビューし、Pyxelのプロンプト入力画面から「もう少しターゲットを狭めたい」「Painの解像度を上げて」など、人間の視点からの修正フィードバックをシステムに介入・入力することができる。

## 7. 非機能要件・オブザーバビリティ (Observability)

### 7.1 LangSmithによるトレースの完全統合

前バージョンで無効化されていたLangSmithトレースをデフォルトで必須要件とする（`extra="ignore"`による環境変数の許容、または明示的なフィールド定義）。

* **目的**:
  1. 仮想顧客テストや3Hレビューにおける無限ループ（デッドロック）の監視とトークン消費の制御。
  2. ステップ間のコンテキスト伝播（Pydanticモデルの変換ロス）のデバッグ。

### 7.2 サーキットブレーカーとハードリミット

マルチエージェント対話（特にSimulationと3H Review）においては、APIの浪費を防ぐため、`max_turns` の設定に加え、特定の文字列表現（例："同意します" "平行線ですね"）を検知して強制終了するモデレーターロジックを挟む。
