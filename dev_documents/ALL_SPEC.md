下記のうち、大部分は実装済みなはずだ。
既存の資産を最大化しつつ、全体最適や実装されていない要素技術をしっかり実装すること。

The JTC 2.0：拡張マルチエージェント・アーキテクチャによるエンタープライズ事業開発のパラダイムシフトイントロダクション：真のエンタープライズ・イノベーション基盤への昇華「The JTC 2.0」のシステム構想は、田所雅之氏の「起業の科学」に代表される厳格なスタートアップ方法論と、日本的伝統企業（JAPAN TRADITIONAL COMPANY：JTC）特有の組織文化・力学を融合させる、極めて野心的なエンタープライズ・アーキテクチャである。LangGraphによるワークフロー制御、LlamaIndexを介したローカル知識の検索拡張生成（RAG）、Tavilyを用いた外部検索、Vector DB、Tool Calling、そしてLangSmithによる監視という最先端の生成AIスタックを統合し、Pyxelを用いた昭和レトロゲーム風のユーザーインターフェース（UI）を被せるというアプローチは、高度な心理的バッファとして機能する可能性を秘めている。しかしながら、このシステムをエンタープライズレベルの真のイノベーション創出エンジンとして機能させるためには、純粋なデジタル空間で完結するマルチエージェントシステムが本質的に抱える「欠落した視点」を補完する必要がある。どれほど高度な外部検索を行っても、最終的には二次情報と大規模言語モデル（LLM）の内部知識の掛け合わせに終始し、「精巧な机上の空論」に陥る危険性が高い。「起業の科学」の原則に従うならば、ビジネスモデルの構築は全自動の出力結果ではなく、**顧客の生の声（一次情報）と、起業家自身の直感と論理に基づく「連続的な意思決定」**の産物でなければならない。本レポートでは、提供されたアーキテクチャ要素技術を最大限に活用し、The JTC 2.0をより強靭かつ実用的なシステムへと昇華させるための拡張理論と実装要件を提示する。具体的には、LangGraphの機能を用いた多段的なHuman-in-the-Loop（HITL）アーキテクチャの定義、プロキシモデルとゲーミフィケーションによる「脱同一化」、寡黙なCPO（Chief Product Officer）エージェントによるメンタリング、French-DeGrootモデルを用いた根回しの数理的シミュレーション、そして外部API連携によるMVP（Minimum Viable Product）自動生成への拡張について、包括的かつ深層的な分析を提供する。「起業の科学」自動化におけるマルチエージェントの高度化と評価指標「起業の科学」における初期フェーズには、課題の探求を行い、ソリューションに予算を投じる「エバンジェリスト（アーリーアダプター）」を発見し、前提条件を検証するプロセスが不可欠である。システムが複雑化するにつれ、単なるテキスト生成の精度だけではその有効性を測ることは不可能となる。合議による「激詰め」や「ピボット」を前提とする場合、多次元的なスコアリング指標をシステム設計の初期段階で組み込む必要がある。評価ディメンション指標の定義と目的The JTC 2.0における実装要件プランニングスコア (Planning Score)メイン課題からサブエージェントへのタスク分割の成功率を測定する。市場調査からペルソナ生成への文脈の引き継ぎが論理的に破綻していないかをLangSmithのトレースで追跡・定量化する。コミュニケーションスコア (Communication Score)タスク完了のためにエージェント間で交わされたメッセージの効率性と妥当性を評価する。「激詰め」プロセスにおいて、無限ループやデッドロックに陥らずに合意形成に至るまでの通信コストとターン数を監視する。ツール選択品質 (Tool Selection Quality)TavilyやローカルVector DBなどの外部ツールを、適切なパラメータで正確に呼び出せたかを評価する。外部市場データが必要な場面でLLMの内部知識（幻覚）に頼らず、意図的かつ正確にTool Callingを実行したかを判定する。アクション完了率 (Action Completion)ユーザーの目標を完全に達成し、明確な回答や確認を提供できたかの割合を測定する。出力される仮説やプロンプトが、起業の科学のフォーマットを満たし、内部の論理的整合性が取れているかを検証する。認知負荷管理 (Cognitive Load Management)エージェント間でタスクが効率的に分散され、コンテキストウィンドウの枯渇や過負荷を防げているかを測定する。大量の社内ドキュメントや一次情報（議事録）参照時に、情報の要約とチャンク化が適切に行われているかを監視する。連続的Human-in-the-Loop（HITL）：起業の科学に準拠した4つの意思決定ゲートマルチエージェントシステムの最大の弱点である「机上の空論」を回避するためには、LangGraphの interrupt() パターンを活用し、システムが自律的に進むプロセスを意図的に一時停止（Suspend）させ、人間の判断と実社会の一次情報をシステムに強制注入する「意思決定ゲート」を設ける必要がある 。「起業の科学」のフレームワークに従い、The JTC 2.0は以下の4つのフェーズにおいて、ユーザー（プレイヤー）に極めて重要な意思決定を要求する設計とする。ゲート1：Idea Verification（最善の仮説「Plan A」の選定）最初のフェーズにおいて、マルチエージェントは市場調査やPEST分析をもとに、10個の「リーンキャンバス」の素案を自動生成する。ここでシステムは最初の interrupt() を実行し、進行を停止する。ユーザーは、PyxelのUI上で提示された10個のアイデアに対し、以下の「起業の科学」の基準に照らし合わせて**ただ1つの「Plan A」**を選定（あるいは組み合わせによる修正）する意思決定を下す。Good Crazyの判定： 誰が聞いても良いアイデア（すでに大企業が着手しているレッドオーシャン）ではなく、一見バカげているが理にかなっているか。Why Now（タイミング）： PEST分析の変曲点（法改正、新技術など）によって、今やる必然性があるか。Founder-Market Fit： ユーザー自身（またはチーム）に、その課題を解くための強い原体験やオブセッション（執念）があるか。ゲート2：Customer-Problem Fit（最重要リスクの特定と一次情報の注入）Plan Aが選定されると、エージェントはペルソナとエンパシーマップを構築し、ジャベリンボード（仮説検証ボード）を展開して前提条件を洗い出す。ここでの意思決定は**「Riskiest Assumption（最もリスクの高い前提）」の特定**である。ユーザーは、システムが提示する前提条件の中から「これが間違っていたらビジネスが破綻する」という致命的な仮説を選択する。ここで「出撃命令」が下される。ユーザーは実際にオフィスの外に出て「The Mom Test（過去の事実を聞く質問）」に基づくプロブレムインタビューを実施する。この際、PLAUD NOTEなどのAI議事録ツールを用いて得られた生の会話データ（トランスクリプト）をシステムにインポートする。システムはこれをLlamaIndex経由でチャンク化してVector DBに格納し、ネットの憶測ではなく「実際の顧客の生々しい発言、ため息、不満」に基づいてエンパシーマップを事実ベースに書き換える。ゲート3：Problem-Solution Fit（MVPスコープの「引き算」）課題の深刻度（Burning Needs）が確認された後、システムはUXブループリントを描き、解決策（ソリューション）の提案を行う。ここでシステムは三度目の停止を行う。多くのスタートアップが陥る失敗は、MVP（Minimum Viable Product）に機能を詰め込みすぎることである。ここでのユーザーの重要な意思決定は、**「ワン機能・ワンバリュー」の原則に従い、機能を削ぎ落とす（Nice to haveを除外する）**ことである。システムが提案する機能リストから、ユーザーは「Must-have（なくてはならないコア機能）」を一つだけ選び、LP型、コンシェルジュ型、あるいはオズの魔法使い型といったMVPの「型」を決定する。ゲート4：Product-Market Fit（AARRR評価とピボットの決断）MVPを市場に出した後、AARRR指標（特にActivationとRetention）に基づく計測データがシステムにフィードバックされる。ダッシュボード上で継続率（Retention Curve）が平坦になっていない（底を打っていない）ことが確認された場合、ユーザーは最大の意思決定を迫られる。残存資金（ランウェイ）と1回あたりの検証コストから計算された「残りピボット可能回数」を睨みながら、「辛抱する（Persevere）」か「ピボットする（Pivot）」かを決断する。ピボットする場合は、Zoom-in（機能の一部切り出し）、Zoom-out、顧客セグメントの変更、顧客ニーズの変更など、どの軸足をずらすかの指示をエージェントに与える。プロキシモデルと脱同一化による心理的安全性の構築JTC特有の「激詰め（容赦のない厳しいフィードバック）」は、事業計画の脆弱性を洗い出す上で極めて機能的であるが、提案者の心理的安全性を破壊する。これを解決するのが、ユーザーの立ち位置を「当事者」から「メンター（あるいは黒幕）」へとスライドさせる「プロキシ（代理人）モデル」の導入である。観劇型「地獄の会議」シミュレーションユーザーは上記のゲートで決定した方針を、「JTCの新入社員エージェント（若手特命担当）」というプロキシキャラクターに託す。その後、LangGraphのバックエンドにおいて、新入社員エージェントと部門長エージェント群との間で自律的なバトルが展開される。財務部長エージェントはTavilyで検索した市場データを盾にコスト構造から激詰めを行い、営業本部長エージェントは現場リソースと既存顧客とのカニバリズムの観点から攻撃を仕掛ける。新入社員エージェントは、部門長たちの鋭い指摘の前に防戦一方となり、計画の破綻を露呈する。ユーザーは、Pyxelのレトロなドット絵UIを通じて、この「大炎上している会議」を安全な高台から観戦する。ゲーミフィケーションと「脱同一化」の力学この構図は、心理学における「脱同一化（De-identification）」という防衛緩和メカニズムを機能させる 。自分のアイデアが直接批判されると人は防衛機制を働かせるが、代理人であるキャラクターが怒られている状況を観察する場合、事象は「RPGの主人公が強力なボスに苦戦している」という客観的なゲーム体験へと変換される 。ユーザーは傷つくことなく、心理的バッファに守られた状態で、部門長エージェントたちの指摘（事業計画のリスク）を冷静に受け入れることができる。さらに、前述のPLAUDを介した「一次情報の注入」により、部門長エージェントは「トランスクリプトの[05:24]で、顧客は明らかに価格への抵抗感を示している。君の希望的観測ではないか？」とファクトベースで激詰めを行ってくるため、圧倒的なリアリティとストレステストの強度が担保される。寡黙なCPOエージェントとインフォーマル・ダイナミクスのハック「激詰め」による破壊（減点法）の後には、仮説の再構築（加点法）のフェーズが不可欠である。The JTC 2.0のワークフローに「破壊と再生」のループを完成させる核心的要素が、「寡黙なCPO（Chief Product Officer）エージェント」の実装である。「屋上フェーズ」：非公式コミュニケーションのアルゴリズム化JTCにおいて本質的なメンタリングは、公式な会議室ではなく「タバコ部屋」や「屋上」で行われる。システムはこれをノードとして分離する。会議室フェーズ（公式ノード）では、CPOエージェントは沈黙を保ちつつ、バックグラウンドでTavilyを用いて議論の争点に関する外部検索を実行する。会議後、PyxelのUIは「夕暮れの屋上」へと切り替わる（非公式ノード）。ここでCPOエージェントがこっそりと新入社員（および背後にいるユーザー）に接触し、客観的ファクトに基づく軌道修正のアドバイスを提供する。答えではなく「武器（ファクト）」を渡すCPOの重要な制約は「最終的な答えを出さない」ことである。CPOはプロダクトマネジメント（起業の科学）のアウトサイド・イン（顧客至上主義）の観点から「武器」を提供し、決断はユーザーのHITLゲートに委ねる。「米国の類似課題ではSaaSではなくAPI提供でPMFしている事例がある。UI構築コストを省いてAPIエコノミーにピボットすれば、財務の懸念も突破できる。どうする、決めるのはお前だ」と選択肢を提示することで、ユーザーは「激詰めをデータで論破する」カタルシスを得ることができる。インフォーマル組織ダイナミクスと合意形成の数理モデル化（DeGrootモデル）JTCにおいて、優れたビジネスモデルキャンバスが完成しても、水面下の「根回し（Nemawashi）」プロセスを通過できなければ実行に移されることはない。システムは、このインフォーマルな意思決定ダイナミクスをシミュレーションするため、「French-DeGrootモデル」の拡張アーキテクチャを導入する 。French-DeGrootモデルは、ネットワーク化されたエージェントシステムにおける意見形成（Opinion Dynamics）の標準的な数理モデルであり、エージェントは他者の意見の影響度（重み $w_{ij}$）を加味しながら自らの意見を更新していく 。JTCの部門長エージェントには、自身の意見に対する高い自己効力感（Self-confidence: $w_{ii}$）がパラメータとして設定される 。CPOが提示する「一次情報（PLAUDのトランスクリプト）」や「競合データ」は、この数理モデルにおいて、部門長の自己効力感 $w_{ii}$ を強制的に下げ、外部ファクトへの重み $w_{ij}$ を高めるパラメータとして機能する 。さらにシステムは「飲み会（Nomikai）シミュレーション」として、社会的拒絶リスクが低下するパラメータ環境下での意見動学を計算し、「誰から順に、どのようなファクトを用いてアプローチすべきか」という「根回しマップ」を動的に生成する。構想から実行へ：v0.dev連携によるMVP自動生成と検証ループMVPのスコープが「ワン機能・ワンバリュー」に絞り込まれた後（ゲート3通過後）、The JTC 2.0はLangGraphのTool Calling機能を拡張し、Vercelが提供するAI駆動のUI生成プラットフォーム「v0.dev」のAPIと連携してMVPの自動構築を実行する 。v0.devのPlatform APIおよび @v0-sdk/ai-tools を活用することで、自律型エージェントは自然言語のプロンプトから直接、React、Next.js、Tailwind CSSを用いた本番環境レベルのUIコンポーネントを生成し、テスト用のURLを発行する 。v0は「LLM Suspense」機能により、生成中のコードエラーをリアルタイムで検知・自動修正するため、信頼性の高いフロントエンドを数十分で組み上げることが可能である 。v0が生成するのはフロントエンド（全体の20%）に留まるが 、PSFフェーズにおける「ペーパープロトタイプ」や「高忠実度プロトタイプ」として顧客の反応を引き出す（コミットメントを得る）ための実験ツールとしては完璧に機能する。このMVP生成により、「構築（Build）→ 計測（Measure）→ 学習（Learn）」というリーン・スタートアップのループがかつてない速度で回転し始める。投資家向け指標への変換とガバナンスの確保PMFフェーズを通過した事業案を最終的な社内決裁に乗せるため、The JTC 2.0はBMCを「VC拡張型バランスト・スコアカード」に変換する。LTV > 3 × CAC の黄金律（LTVが顧客獲得単価の3倍以上あるか）や、Payback Period（CACを12ヶ月以内に回収できるか）、ユニットエコノミクスの健全性といった厳しい財務指標をTavilyの外部データから推計する。さらに、LlamaIndexを活用して社内の過去の稟議書データを参照し、AIが自動的に「稟議書」の起案文書を生成する。この一連の高度な自律プロセスをエンタープライズで安全に稼働させるため、LangSmithによる監視に加え、有害性（Toxicity）やバイアスを防ぐ倫理的・技術的ガードレールを多層的に配置することが運用成功の絶対条件となる。結論：自律型エンタープライズ・アクセラレーターの完成「The JTC 2.0」の真の価値は、最新AI技術の寄せ集めではなく、「起業の科学」という厳格なサイエンスを、JTCの複雑な組織力学の中で強制的に実践させるためのシステム設計にある。LangGraphのInterruptパターンによる4つの意思決定ゲートは、システムを机上の空論から救い出し、起業家（ユーザー）の熱量とPLAUDを通じた一次情報に係留する。プロキシモデルとCPOエージェントによるメンタリングは、ユーザーの心を折ることなく「破壊と再生」のピボットループを創出し、French-DeGrootモデルは強固な社内政治をハックする。そしてv0.devによるMVPの即時生成は、検証スピードを極限まで引き上げる。これらの統合により、The JTC 2.0は単なる壁打ちツールを超え、硬直化したエンタープライズの中にアジャイルで強靭なスタートアップの魂を宿らせる「自律型エンタープライズ・アクセラレーター」として完成するのである。


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
