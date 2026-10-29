import { useEffect, useMemo, useState } from "react";
import { getCatalog, listSessions, startSession, stopSession } from "./api";

const STATUS = {
  idle: "свободна",
  busy: "занята",
  running: "идёт заправка",
  completed: "завершено",
  stopped: "остановлено",
};

function money(value) {
  return new Intl.NumberFormat("ru-RU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function liters(value) {
  return new Intl.NumberFormat("ru-RU", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

function clock(value) {
  return new Date(value).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function App() {
  const [catalog, setCatalog] = useState(null);
  const [history, setHistory] = useState([]);
  const [pumpId, setPumpId] = useState(null);
  const [fuelId, setFuelId] = useState(null);
  const [tariffId, setTariffId] = useState(null);
  const [mode, setMode] = useState("liters");
  const [value, setValue] = useState("20");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  useEffect(() => {
    let ignore = false;

    async function load() {
      try {
        const [nextCatalog, nextHistory] = await Promise.all([getCatalog(), listSessions()]);
        if (ignore) return;
        setCatalog(nextCatalog);
        setHistory(nextHistory);
        setPumpId((current) => current ?? nextCatalog.pumps[0]?.id ?? null);
        setFuelId((current) => current ?? nextCatalog.fuels[0]?.id ?? null);
        setTariffId((current) => current ?? nextCatalog.tariffs[0]?.id ?? null);
        setError("");
      } catch (err) {
        if (!ignore) setError(err.message);
      }
    }

    load();
    const timer = setInterval(load, 500);
    return () => {
      ignore = true;
      clearInterval(timer);
    };
  }, []);

  const pump = catalog?.pumps.find((item) => item.id === pumpId) ?? null;
  const fuel = catalog?.fuels.find((item) => item.id === fuelId) ?? null;
  const tariff = catalog?.tariffs.find((item) => item.id === tariffId) ?? null;
  const active = pump?.active_session ?? null;

  const quote = useMemo(() => {
    if (!fuel || !tariff) return null;
    const price = Math.round(fuel.price * (1 - tariff.discount_percent / 100) * 100) / 100;
    const amount = Number(value);
    if (!Number.isFinite(amount) || amount <= 0) return { price, liters: 0, total: 0 };
    if (mode === "liters") {
      return { price, liters: amount, total: Math.round(amount * price * 100) / 100 };
    }
    return { price, liters: amount / price, total: amount };
  }, [fuel, tariff, mode, value]);

  const shownLiters = active ? active.dispensed_liters : quote?.liters ?? 0;
  const shownTotal = active ? active.dispensed_total : quote?.total ?? 0;
  const progress = active ? active.progress : 0;

  async function onStart(event) {
    event.preventDefault();
    if (!pump || !fuel || !tariff || pump.status === "busy") return;
    setPending(true);
    setError("");
    try {
      await startSession({
        pump_id: pump.id,
        fuel_id: fuel.id,
        tariff_id: tariff.id,
        mode,
        value: Number(value),
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setPending(false);
    }
  }

  async function onStop() {
    if (!active) return;
    setPending(true);
    setError("");
    try {
      await stopSession(active.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="page">
      <header className="top">
        <div className="brand">
          <span className="badge">АЗС</span>
          <div>
            <p className="eyebrow">симулятор колонки</p>
            <h1>Бенз</h1>
          </div>
        </div>
        <p className="lede">Топливо, тариф и объём. Колонка льёт около 1,8 л/с, запись остаётся в базе.</p>
      </header>

      {!catalog && <p className="banner">Подключение к станции…</p>}
      {error && <p className="banner error">{error}</p>}

      {catalog && (
        <>
          <section className="pumps" aria-label="Колонки">
            {catalog.pumps.map((item) => (
              <button
                key={item.id}
                type="button"
                className={item.id === pumpId ? "pump selected" : "pump"}
                onClick={() => setPumpId(item.id)}
              >
                <span>Колонка {item.number}</span>
                <strong className={item.status}>{STATUS[item.status]}</strong>
              </button>
            ))}
          </section>

          <section className="layout">
            <div className="panel display">
              <div className="display-head">
                <span>Колонка {pump?.number}</span>
                <span className={active ? active.status : "idle"}>
                  {active ? STATUS[active.status] : "ожидание"}
                </span>
              </div>
              <p className="label">литры</p>
              <p className="digits">{liters(shownLiters)}</p>
              <p className="label">сумма, ₽</p>
              <p className="digits money">{money(shownTotal)}</p>
              <div className="track" aria-hidden="true">
                <div style={{ width: `${Math.round(progress * 100)}%` }} />
              </div>
              <p className="meta">
                {active
                  ? `${active.fuel_name} · ${active.tariff_name} · ${money(active.price_per_liter)} ₽/л`
                  : quote
                    ? `${fuel.name} · ${tariff.name} · ${money(quote.price)} ₽/л`
                    : "Выберите топливо"}
              </p>
            </div>

            <form className="panel form" onSubmit={onStart}>
              <fieldset disabled={Boolean(active) || pending}>
                <legend>Топливо</legend>
                <div className="choices">
                  {catalog.fuels.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className={item.id === fuelId ? "choice on" : "choice"}
                      onClick={() => setFuelId(item.id)}
                    >
                      <span>{item.name}</span>
                      <small>{money(item.price)} ₽</small>
                    </button>
                  ))}
                </div>
              </fieldset>

              <fieldset disabled={Boolean(active) || pending}>
                <legend>Тариф</legend>
                <div className="choices">
                  {catalog.tariffs.map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className={item.id === tariffId ? "choice on" : "choice"}
                      onClick={() => setTariffId(item.id)}
                    >
                      <span>{item.name}</span>
                      <small>{item.discount_percent ? `−${item.discount_percent}%` : "без скидки"}</small>
                    </button>
                  ))}
                </div>
              </fieldset>

              <fieldset disabled={Boolean(active) || pending}>
                <legend>Сколько</legend>
                <div className="modes">
                  <button
                    type="button"
                    className={mode === "liters" ? "choice on" : "choice"}
                    onClick={() => setMode("liters")}
                  >
                    Литры
                  </button>
                  <button
                    type="button"
                    className={mode === "money" ? "choice on" : "choice"}
                    onClick={() => setMode("money")}
                  >
                    Рубли
                  </button>
                </div>
                <label className="amount">
                  {mode === "liters" ? "Литры" : "Сумма, ₽"}
                  <input
                    inputMode="decimal"
                    value={value}
                    onChange={(event) => setValue(event.target.value.replace(",", "."))}
                  />
                </label>
              </fieldset>

              {active?.status === "running" ? (
                <button type="button" className="go stop" onClick={onStop} disabled={pending}>
                  Остановить
                </button>
              ) : (
                <button type="submit" className="go" disabled={pending || pump?.status === "busy"}>
                  Занять колонку
                </button>
              )}
            </form>
          </section>

          <section className="panel history">
            <h2>Последние заправки</h2>
            {history.length === 0 ? (
              <p className="empty">Пока пусто — первая заправка появится здесь.</p>
            ) : (
              <table>
                <thead>
                  <tr>
                    <th>Когда</th>
                    <th>Колонка</th>
                    <th>Топливо</th>
                    <th>Тариф</th>
                    <th>Литры</th>
                    <th>Сумма</th>
                    <th>Статус</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((row) => (
                    <tr key={row.id}>
                      <td>{clock(row.started_at)}</td>
                      <td>{row.pump_number}</td>
                      <td>{row.fuel_name}</td>
                      <td>{row.tariff_name}</td>
                      <td>{liters(row.dispensed_liters)}</td>
                      <td>{money(row.dispensed_total)} ₽</td>
                      <td>{STATUS[row.status]}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}
    </div>
  );
}
