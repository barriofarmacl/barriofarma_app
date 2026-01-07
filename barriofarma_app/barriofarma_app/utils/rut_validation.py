# -*- coding: utf-8 -*-
# Copyright (c) 2026, Barrio Farma and Contributors
# See license.txt

"""
Utilidades para validación de RUT chileno.

Formato RUT chileno: XX.XXX.XXX-X o XXXXXXXX-X
Donde X son dígitos y el último es el dígito verificador (0-9 o K)
"""

import re
import frappe
from frappe import _


def validate_rut_format(rut):
	"""
	Valida el formato de un RUT chileno.
	
	Args:
		rut: String con el RUT a validar
		
	Returns:
		tuple: (is_valid, cleaned_rut, error_message)
		- is_valid: True si el formato es válido
		- cleaned_rut: RUT sin puntos ni guiones (solo números y K)
		- error_message: Mensaje de error si no es válido
	"""
	if not rut:
		return False, None, _("RUT no puede estar vacío")
	
	# Limpiar RUT: remover puntos, espacios y guiones
	cleaned_rut = re.sub(r'[.\s-]', '', rut.strip().upper())
	
	# Validar formato: debe tener al menos 7 dígitos + 1 dígito verificador
	# Formato: números + K o número al final
	if not re.match(r'^\d{7,8}[0-9K]$', cleaned_rut):
		return False, None, _("Formato de RUT inválido. Debe ser XX.XXX.XXX-X o XXXXXXXX-X")
	
	# Separar número y dígito verificador
	number = cleaned_rut[:-1]
	verifier = cleaned_rut[-1]
	
	# Validar dígito verificador
	if not validate_rut_verifier(number, verifier):
		return False, None, _("RUT inválido: el dígito verificador no coincide")
	
	return True, cleaned_rut, None


def validate_rut_verifier(number, verifier):
	"""
	Valida el dígito verificador de un RUT chileno.
	
	Algoritmo:
	1. Multiplicar cada dígito por la secuencia 2, 3, 4, 5, 6, 7 (repetir si es necesario)
	2. Sumar todos los productos
	3. Calcular 11 - (suma % 11)
	4. Si resultado es 11, dígito es 0; si es 10, dígito es K; sino es el resultado
	
	Args:
		number: Número del RUT (sin dígito verificador)
		verifier: Dígito verificador (0-9 o K)
		
	Returns:
		bool: True si el dígito verificador es válido
	"""
	try:
		# Revertir el número para procesar de derecha a izquierda
		reversed_number = number[::-1]
		
		# Secuencia de multiplicadores
		multipliers = [2, 3, 4, 5, 6, 7]
		
		# Calcular suma
		total = 0
		for i, digit in enumerate(reversed_number):
			multiplier = multipliers[i % len(multipliers)]
			total += int(digit) * multiplier
		
		# Calcular dígito verificador esperado
		remainder = total % 11
		expected_verifier = 11 - remainder
		
		# Ajustar según reglas
		if expected_verifier == 11:
			expected_verifier = 0
		elif expected_verifier == 10:
			expected_verifier = 'K'
		else:
			expected_verifier = str(expected_verifier)
		
		# Comparar con el verificador proporcionado
		return str(verifier) == str(expected_verifier)
	except (ValueError, IndexError):
		return False


def format_rut(rut):
	"""
	Formatea un RUT chileno con puntos y guión.
	
	Args:
		rut: RUT sin formato o con formato
		
	Returns:
		str: RUT formateado (XX.XXX.XXX-X)
	"""
	if not rut:
		return ""
	
	# Limpiar RUT
	cleaned_rut = re.sub(r'[.\s-]', '', rut.strip().upper())
	
	if len(cleaned_rut) < 8:
		return rut  # Retornar original si no tiene formato válido
	
	# Separar número y dígito verificador
	number = cleaned_rut[:-1]
	verifier = cleaned_rut[-1]
	
	# Formatear con puntos
	# Si tiene 7 dígitos: X.XXX.XXX
	# Si tiene 8 dígitos: XX.XXX.XXX
	if len(number) == 7:
		formatted = f"{number[0]}.{number[1:4]}.{number[4:]}-{verifier}"
	else:
		formatted = f"{number[0:2]}.{number[2:5]}.{number[5:]}-{verifier}"
	
	return formatted

