API reference
=============

The entire public API is re-exported from the top-level ``asyoulikeit``
package, so ``from asyoulikeit import Report, Reports, report_output``
is the intended import path. The sub-module documentation below is for
readers who want the full picture.

Top-level package
-----------------

.. automodule:: asyoulikeit
   :members:
   :imported-members:
   :exclude-members: ALL_REPORTS


Report content: the base
------------------------

.. automodule:: asyoulikeit.content
   :members:
   :show-inheritance:


Table content
-------------

.. automodule:: asyoulikeit.tabular_data
   :members:
   :show-inheritance:


Tree content
------------

.. automodule:: asyoulikeit.tree_data
   :members:
   :show-inheritance:


Scalar content
--------------

.. automodule:: asyoulikeit.scalar_data
   :members:
   :show-inheritance:


The report-output decorator
---------------------------

.. automodule:: asyoulikeit.cli
   :members:
   :show-inheritance:


Formatters
----------

.. automodule:: asyoulikeit.formatter
   :members:
   :show-inheritance:


Extension machinery
-------------------

.. automodule:: asyoulikeit.extension
   :members:
   :show-inheritance:


Exceptions
----------

.. automodule:: asyoulikeit.exceptions
   :members:
   :show-inheritance:
