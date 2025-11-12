# Changelog

## [1.0.8](https://github.com/agrc/open-sgid/compare/v1.0.7...v1.0.8) (2025-11-12)


### Dependencies

* **dev:** update pytest-cov requirement from ==6.* to &gt;=6,&lt;8 ([ecfe5c4](https://github.com/agrc/open-sgid/commit/ecfe5c4e8e4503b0b589463e36155ebcdcc0a0f9))


### Documentation

* add required information for inserting new data ([9b1acc6](https://github.com/agrc/open-sgid/commit/9b1acc622dab5380951d8aa576224361f8856a03))

## [1.0.7](https://github.com/agrc/open-sgid/compare/v1.0.6...v1.0.7) (2025-08-21)


### Bug Fixes

* update database code to be more resilient ([7d945bb](https://github.com/agrc/open-sgid/commit/7d945bbeb050b844611037e07fe1489784da0594))

## [1.0.6](https://github.com/agrc/open-sgid/compare/v1.0.5...v1.0.6) (2025-08-21)


### Bug Fixes

* remove newlines from text ([59093db](https://github.com/agrc/open-sgid/commit/59093db57e637079757a5bb7d98c8e92ba676091))

## [1.0.5](https://github.com/agrc/open-sgid/compare/v1.0.4...v1.0.5) (2025-08-21)


### Bug Fixes

* improve last checked ([56b5447](https://github.com/agrc/open-sgid/commit/56b54471e27deb1393558cf513e9c923f42455db))

## [1.0.4](https://github.com/agrc/open-sgid/compare/v1.0.3...v1.0.4) (2025-08-21)


### Bug Fixes

* log check text string value ([70f2511](https://github.com/agrc/open-sgid/commit/70f2511f4610000a961140d9de64f6f41d586ced))

## [1.0.3](https://github.com/agrc/open-sgid/compare/v1.0.2...v1.0.3) (2025-08-21)


### Bug Fixes

* add logging around last checked date ([64a0e9d](https://github.com/agrc/open-sgid/commit/64a0e9dc53d40dde83ecd21c87765b7110f75036))

## [1.0.2](https://github.com/agrc/open-sgid/compare/v1.0.1...v1.0.2) (2025-08-21)


### Bug Fixes

* update logging to give more details ([b11cbc7](https://github.com/agrc/open-sgid/commit/b11cbc7eb6afccdb96b957bc14b147827d90619b))

## [1.0.1](https://github.com/agrc/open-sgid/compare/v1.0.0...v1.0.1) (2025-05-14)


### Dependencies

* **dev:** update pytest-cov requirement ([e2e5ff8](https://github.com/agrc/open-sgid/commit/e2e5ff81ef028ed98f20fd7b35b5ec0914614856))
* **dev:** update pytest-cov requirement from ==5.* to &gt;=5,&lt;7 ([#73](https://github.com/agrc/open-sgid/issues/73)) ([dc561e8](https://github.com/agrc/open-sgid/commit/dc561e8dfa610177e6e52070de2a64935ac03206))
* fy25q4 package updates ([c1d13a9](https://github.com/agrc/open-sgid/commit/c1d13a9af1a3d5a0762dbd1aa37b6d71c787987a))


### Documentation

* update database versions ([43cbbf9](https://github.com/agrc/open-sgid/commit/43cbbf90712b30c542c25ea4a901da8d2490b686))

## 1.0.0 (2024-10-15)


### Features

* add date to log strings ([d159cea](https://github.com/agrc/open-sgid/commit/d159cea9457c9041e0fa99a5f1dbb1fe8a9654dc))
* add drop schema command ([d049f0c](https://github.com/agrc/open-sgid/commit/d049f0ca78608ebbdfd5faf15e1e6c8780b9e845))
* add indexes for parcel searches ([54ca10b](https://github.com/agrc/open-sgid/commit/54ca10bef04f6dffebbf32e4ff885ee3e5b8dea7))
* add logger, verbosity cli option, dry-run and skip if exists ([dd70845](https://github.com/agrc/open-sgid/commit/dd70845a7f813bfce36ee080f66f8e25ada3f1ee))
* add timing logs ([2cf8ca5](https://github.com/agrc/open-sgid/commit/2cf8ca5471041f9f791384c8b0dd86978dd9a3f9))
* add trim and import --missing ([f4aa215](https://github.com/agrc/open-sgid/commit/f4aa215fcde704d2e52183f615d2a2b241f282cb))
* colors and skip schema ([ecf500a](https://github.com/agrc/open-sgid/commit/ecf500a9f247f98f823b1b529a57c844159f15fe))
* create db with terraform ([a211cf1](https://github.com/agrc/open-sgid/commit/a211cf10ea06a03762cb15432a3ab4b3ecc5f743))
* create indexes ([f967e49](https://github.com/agrc/open-sgid/commit/f967e49da5e9104051ffc81ffb1beaaa63b9dcc3))
* create read only user and set geometry types specifically ([efeea7c](https://github.com/agrc/open-sgid/commit/efeea7c688d8f4ab0e55155dce686502b0459a0a))
* import geometries correctly the first time ([0961c8b](https://github.com/agrc/open-sgid/commit/0961c8b9040156ec9413d8e5e6b95a32c1c1f183))
* run make valid on imported data ([acbb053](https://github.com/agrc/open-sgid/commit/acbb05344c44b6a9f1035af3c10ca68a9a139bd4))
* smart pluralization of log messages ([1aa4b83](https://github.com/agrc/open-sgid/commit/1aa4b83ad8112adbe9cd5217bd25a45be0386782))
* stop ignoring global id's in open sgid ([0259166](https://github.com/agrc/open-sgid/commit/025916656a0d7b45507faf75a8f65d78f98a8020))
* try set srid on import ([10ffa84](https://github.com/agrc/open-sgid/commit/10ffa84444c17e99391e57b67e4242130b442420))
* try to use meta table to set geometry type ([6074fe3](https://github.com/agrc/open-sgid/commit/6074fe3475f6cabafdd7a1e8a4456119a7f29ecf))
* update specific tables ([a24f630](https://github.com/agrc/open-sgid/commit/a24f630c843a38b1ba4c477173151fb23bf0e827))
* use change detection to figure out what tables to update ([1824b0e](https://github.com/agrc/open-sgid/commit/1824b0ef6a9f0d6725ada763c0dca8e25aa506d8))
* use internal table names ([2fee526](https://github.com/agrc/open-sgid/commit/2fee526083a58ea15f24884dcf8144a30244f4a3))


### Bug Fixes

* --skip-if-exists testing wrong table name ([50e6cd5](https://github.com/agrc/open-sgid/commit/50e6cd5c898bc9c451ff4ffbd79bcc17d24f6dea))
* add else ([50f093d](https://github.com/agrc/open-sgid/commit/50f093d01a72652095bdc32793c0efcafa20fd63))
* color wrapping ([4995744](https://github.com/agrc/open-sgid/commit/4995744a845a89743384a06ecec4d60aa49cf84f))
* correct db table name ([ac98ee4](https://github.com/agrc/open-sgid/commit/ac98ee4ba3a4edf4240e716f890b886701996d3e))
* crash when connection closes ([550e955](https://github.com/agrc/open-sgid/commit/550e95538d334f703e7f841e02c6fc0155c13ffa))
* create methods to alter schemas based on original types ([21f6017](https://github.com/agrc/open-sgid/commit/21f601768e878eec5a50812e49c92df45815a192)), closes [#19](https://github.com/agrc/open-sgid/issues/19)
* destructuring ([c68dbfe](https://github.com/agrc/open-sgid/commit/c68dbfef081cdfa0f75d452219de88fe97985985))
* downgrade pgadmin4 because of boot issue ([905f9fd](https://github.com/agrc/open-sgid/commit/905f9fdd329d4f791b52535142a5627fed1cd541))
* exclude excluded agol item id items ([e1a8af2](https://github.com/agrc/open-sgid/commit/e1a8af2347f33baa92c7ef5f9ce1a5b9cfa632eb))
* execute sql params ([a6148ba](https://github.com/agrc/open-sgid/commit/a6148ba3f2c7835f68ef9a10f096f5786b9a7bf1))
* grant usage ([65207d1](https://github.com/agrc/open-sgid/commit/65207d11c89c4ea159bff84a935845ec7e68f223))
* handle non spatial tables ([468342d](https://github.com/agrc/open-sgid/commit/468342de7de8ede5ccce14ab2c8f6fc77f16da02))
* id name clash ([df9dc94](https://github.com/agrc/open-sgid/commit/df9dc9425f236dab92842d6f5662853d7dcf4af2))
* make password sensitive ([ef2f51c](https://github.com/agrc/open-sgid/commit/ef2f51cfda00351886a4a89911e45473e70f54ef))
* method name ([0a0a351](https://github.com/agrc/open-sgid/commit/0a0a351b7e9036559a2738cda809cf58b445f6d0))
* quote tables to handle special characters ([dd9bcd4](https://github.com/agrc/open-sgid/commit/dd9bcd45e992cf4353573a5bfbf1ac69bd5943d4))
* remove breakpoint ([7f4ec83](https://github.com/agrc/open-sgid/commit/7f4ec83c2eece6688b9efdb49106df744813c63a))
* remove debug cruft ([374a882](https://github.com/agrc/open-sgid/commit/374a8829da9049e5c8677356c7ecc76b960e2a88))
* removing too many utah's ([bae9f42](https://github.com/agrc/open-sgid/commit/bae9f428ea3b2c9fd385d1a4afb6419169e6c31e))
* reverse lookup origin tables for missing ([fe81de6](https://github.com/agrc/open-sgid/commit/fe81de67aa8bf21cb6b9a1364ff42cd4a65c14d2))
* skip altering tables with no affected columns ([f552c00](https://github.com/agrc/open-sgid/commit/f552c00477af801ca77bed2fa98863cf9a83c100))
* skip unfixable layers ([9b9ad70](https://github.com/agrc/open-sgid/commit/9b9ad7011b6b3d26a6a13da043bfd728ffb12a15))
* syntax ([bb01f7d](https://github.com/agrc/open-sgid/commit/bb01f7d06cd2244eb0bb2709e457b2dd425bd77a))
* **trim:** dismiss views from postgis public schema ([aa1bb6d](https://github.com/agrc/open-sgid/commit/aa1bb6d9b79700839104182625a82495365cba92))
* try to escape reserved words ([5b8dd52](https://github.com/agrc/open-sgid/commit/5b8dd5239851dfc8d15b34828a3ee3aa57f9aa20))
* try to set default priviliges for all newly created tables ([3a35a20](https://github.com/agrc/open-sgid/commit/3a35a20cc9c34ecfd0f94bd7a004595fe62fc553))
* try to set srid on import ([1eb40b8](https://github.com/agrc/open-sgid/commit/1eb40b80c9e3e7765c3378e6ca561dca908b8444))
* unpacking error ([73d5980](https://github.com/agrc/open-sgid/commit/73d59808e5c9f14a4b695ff57df780007f0d8c44))
* update cli to work around docopt bug ([dd76afd](https://github.com/agrc/open-sgid/commit/dd76afdc21d3c849ce53dd3f62e1adad75b2ea84))
* use full so sql server driver is registered ([4130766](https://github.com/agrc/open-sgid/commit/41307668a7ccf28c4ecbc8b11607196421c2e815))
* variable hoisting and incorrect table name ([45f9b39](https://github.com/agrc/open-sgid/commit/45f9b39965beb7e6e80708aea2b5da610d5ab98f))


### Dependencies

* **dev:** update gunicorn requirement in the major-dependencies group ([f002cc0](https://github.com/agrc/open-sgid/commit/f002cc051437662af31587f4f5731a1332d8b5d3))
* feb updates ([305dc58](https://github.com/agrc/open-sgid/commit/305dc58023b06ba1f44558cb440c9bc173e89cc4))
* FY25 Q2 dependency updates 🌲 ([55a0f87](https://github.com/agrc/open-sgid/commit/55a0f878b70404b86042c098aca5a3d0d2e1570a))
* q4 package updates ([39c51fe](https://github.com/agrc/open-sgid/commit/39c51fe252ccab818d534d8868a0f9ef9c5c253d))
* update gdal image ([121e50a](https://github.com/agrc/open-sgid/commit/121e50a1885409e076db73f5a97ad69fddc524c7))
* update gdal version ([94400ad](https://github.com/agrc/open-sgid/commit/94400add334ff0407556882770e3e36da68e6ac8))


### Documentation

* add database name ([66985a3](https://github.com/agrc/open-sgid/commit/66985a31f03e579fc62cdea5dc77b215881b3685))
* add some version and minimum requirements ([f99c294](https://github.com/agrc/open-sgid/commit/f99c294cd05035d15d9ea46faff52fb40ea2ae50))
* add TOS and connection information ([b65092f](https://github.com/agrc/open-sgid/commit/b65092fe4cef25e8beb77311a6e7f8a9f59868c2))
* add venv info ([39ff63e](https://github.com/agrc/open-sgid/commit/39ff63ef767a92240fbee1e176f151c7ff8e8137))
* be more specific ([c51820a](https://github.com/agrc/open-sgid/commit/c51820a04cb1fc1ae0fa3276a35f611d3f47a7cf))
* **cloudb:** update usage ([5fe9188](https://github.com/agrc/open-sgid/commit/5fe91885f512eff93046a6bd770a2a4956a8f6d8))
* fix format ([aedea54](https://github.com/agrc/open-sgid/commit/aedea54cea11bcac2d06d8b5031b9bcf772ab298))
* fix issue link ([b396c9e](https://github.com/agrc/open-sgid/commit/b396c9e538f417823d7a5e2ab4de8e63870bbb56))
* fix links ([4df9312](https://github.com/agrc/open-sgid/commit/4df9312ba7af7defbf7a8a490281aa7afae62bca))
* initialize terrafrom ([5193f1c](https://github.com/agrc/open-sgid/commit/5193f1c84c697e404660c2361cd46f679457fae6))
* new import ([4193c8d](https://github.com/agrc/open-sgid/commit/4193c8d877926bfa9135e021ab91dc73b51f6938))
* remove cli docs ([a4b1f7d](https://github.com/agrc/open-sgid/commit/a4b1f7dec2f46e2e2dc63600c973fc4f24658867))
* split doc ([6f8a58b](https://github.com/agrc/open-sgid/commit/6f8a58b36fcb34b144b305170e76f5e2a7f81304))
* terraform usage ([999b735](https://github.com/agrc/open-sgid/commit/999b7355b35acd04f7bf49f5f657181071b10035))
* transforming this into the open sgid tracker ([bb8bff9](https://github.com/agrc/open-sgid/commit/bb8bff9d2257baf549d186ce5894a65efc8bb978))
* update local installation ([e8ac0b2](https://github.com/agrc/open-sgid/commit/e8ac0b2c402f49cfe4f90db9fc1556d2ee7cfae1))
* update readme ([d32e2ce](https://github.com/agrc/open-sgid/commit/d32e2ce756932356e7deab1fc550a55a82f71ab1))
* update readme ([b1be23d](https://github.com/agrc/open-sgid/commit/b1be23d99be523648c8e3b88aeeb3baefd102d7e))


### Styles

* fix linting errors ([1e9cbc5](https://github.com/agrc/open-sgid/commit/1e9cbc5d76a2edc6fdeed621cfe461515db007b0))
* single quotes ([088a79d](https://github.com/agrc/open-sgid/commit/088a79dc37a23f0dbcf73f0f28e58dd0744c6020))
* update colors ([42bc6c8](https://github.com/agrc/open-sgid/commit/42bc6c854fb7aff2c65b276578e6bdc5e804c3f2))
* update print statements ([60fcd56](https://github.com/agrc/open-sgid/commit/60fcd560f7fadb37c5f16640510d9c24b5810b99))
