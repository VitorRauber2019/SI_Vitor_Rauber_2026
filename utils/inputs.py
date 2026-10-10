import functools
import re

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

# Faixas de emojis / pictogramas (não inclui letras acentuadas, º, ª, ç etc.)
_EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FAFF"  # emoticons, símbolos, pictogramas, bandeiras
    "☀-➿"          # símbolos diversos e dingbats
    "⬀-⯿"          # setas e símbolos (⭐, ⬆ ...)
    "\U000E0020-\U000E007F"  # tags (bandeiras de subdivisões)
    "︎️"           # seletores de variação
    "‍"                 # zero width joiner
    "⃣"                 # keycap
    "]+"
)

# Mesma regra, para o navegador
_SCRIPT_JS = r"""
<script>
(function () {
  if (window.__padraoInputs) return;
  window.__padraoInputs = true;

  var EMOJI = /[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{E0020}-\u{E007F}\u{FE0E}\u{FE0F}\u{200D}\u{20E3}]+/gu;
  var setters = {
    INPUT: Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set,
    TEXTAREA: Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, "value").set
  };

  document.addEventListener("input", function (e) {
    var el = e.target;
    if (e.isComposing || !el || !el.closest) return;
    if (!el.closest('[data-testid="stTextInput"], [data-testid="stTextArea"]')) return;
    if (el.tagName === "INPUT" && el.type !== "text") return;

    var label = (el.getAttribute("aria-label") || "").toLowerCase();
    var ehEmail = label.indexOf("e-mail") !== -1 || label.indexOf("email") !== -1;

    var atual = el.value;
    var limpo = atual.replace(EMOJI, "");
    limpo = ehEmail ? limpo.toLowerCase() : limpo.toUpperCase();
    if (limpo === atual) return;

    var cursor = el.selectionStart;
    var antesCursor = atual.slice(0, cursor).replace(EMOJI, "").length;
    setters[el.tagName].call(el, limpo);
    el.dispatchEvent(new Event("input", { bubbles: true }));
    try { el.setSelectionRange(antesCursor, antesCursor); } catch (err) {}
  }, true);
})();
</script>
"""


def remover_emojis(texto: str) -> str:
    return _EMOJI_RE.sub("", texto)


def _eh_email(label) -> bool:
    label = str(label or "").lower()
    return "e-mail" in label or "email" in label


def sanitizar(texto, label=None):
    """Remove emojis e deixa em maiúsculo (e-mails ficam em minúsculo)."""
    if not isinstance(texto, str):
        return texto
    texto = remover_emojis(texto)
    return texto.lower() if _eh_email(label) else texto.upper()


def _embrulhar(funcao):
    if getattr(funcao, "_padrao_inputs", False):
        return funcao

    @functools.wraps(funcao)
    def wrapper(*args, **kwargs):
        # Métodos da classe recebem self antes do label
        args_label = args[1:] if args and isinstance(args[0], DeltaGenerator) else args
        label = kwargs.get("label", args_label[0] if args_label else None)
        return sanitizar(funcao(*args, **kwargs), label)

    wrapper._padrao_inputs = True
    return wrapper


def aplicar_padrao_inputs():
    """Força MAIÚSCULO e bloqueia emojis em todos os text_input/text_area.

    Deve ser chamada logo após st.set_page_config em cada página.
    """
    DeltaGenerator.text_input = _embrulhar(DeltaGenerator.text_input)
    DeltaGenerator.text_area = _embrulhar(DeltaGenerator.text_area)
    # st.text_input / st.text_area são métodos já ligados ao DG principal
    st.text_input = _embrulhar(st.text_input)
    st.text_area = _embrulhar(st.text_area)

    st.html(_SCRIPT_JS, unsafe_allow_javascript=True)
